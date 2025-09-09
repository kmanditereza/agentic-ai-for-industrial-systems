# agents/orchestrator_agent/agent.py
import os
import uuid
import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
import anthropic
import dotenv
import re
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import Tool

load_dotenv()

from shared.a2a.task_manager import InMemoryTaskManager
from shared.models.request import SendTaskRequest, SendTaskResponse
from shared.models.task import Message, TaskStatus, TaskState, TextPart
from agents.orchestrator_agent.agent_connect import AgentConnector
from shared.models.agent import AgentCard

logger = logging.getLogger(__name__)


class ProductionAssistantResponse(BaseModel):
    decision: str
    reasoning: str
    sufficient_materials: bool
    machine_states: Dict[str, str]
    material_availability: Dict[str, float]
    tools_used: List[str]


class OrchestratorAgent:
    """
    Uses a langchain and Claude LLM to route incoming user queries,
    calling out to any discovered child A2A agents via tools.
    """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(
        self, 
        agent_cards: list[AgentCard],
        model: str = "claude-3-5-sonnet-20241022",
        verbose: bool = False,
        child_agent_timeout: float = 30.0
    ):
        # Build one AgentConnector per discovered AgentCard
        self.connectors = {
            card.name: AgentConnector(card.name, card.url)
            for card in agent_cards
        }
        
        # Store timeout for child agent calls
        self.child_agent_timeout = child_agent_timeout
        
        # Initialize the LLM
        self.llm = ChatAnthropic(model=model)
        
        # Initialize the parser
        self.parser = PydanticOutputParser(pydantic_object=ProductionAssistantResponse)
        
        # Create the prompt template
        self.prompt = self._create_prompt_template()

        # Create proper LangChain tools
        self.tools = self._create_tools()
        
        # Create the agent and executor
        self.agent = create_tool_calling_agent(
            llm=self.llm, 
            prompt=self.prompt, 
            tools=self.tools
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=verbose,
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=False
        )

    def _create_tools(self) -> List[Tool]:
        """Create proper LangChain Tool objects."""
        
        list_agents_tool = Tool(
            name="list_agents",
            description="List all available child agents that can help with the task",
            func=self._list_agents
        )
        
        delegate_task_tool = Tool(
            name="delegate_task",
            description=(
                "Delegate a task to a specific child agent. "
                "The input should be formatted as: agent_name|message|session_id "
                "Example: 'MaterialCalculatingAgent|Calculate materials for 3 batches of Product A|session123'"
            ),
            func=self._delegate_task_sync
        )
        
        return [list_agents_tool, delegate_task_tool]

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create the prompt template."""
        agent_list = "\n".join(f"- {name}" for name in self.connectors) if self.connectors else "- No agents available"
        
        return ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an Orchestrator Agent for Batch Plant Planning. Your job is to determine if the plant can produce a specified number of batches for a given product.

Available child agents:
{agent_list}

IMPORTANT INSTRUCTIONS:
1. ALWAYS use delegate_task tool TWICE to gather information:
   - First: delegate to MaterialCalculatingAgent to calculate material requirements
   - Second: delegate to EquipmentMonitoringAgent to check material levels and machine states

2. Format for delegate_task: "AgentName|message|session_id"
   - MaterialCalculatingAgent example: "MaterialCalculatingAgent|Calculate materials for 3 batches of Product A|session123"
   - EquipmentMonitoringAgent example: "EquipmentMonitoringAgent|Check current material levels and machine states|session123"

3. After receiving responses from BOTH agents, analyze the data and make a decision.

4. YOUR FINAL OUTPUT MUST BE **ONLY** A VALID JSON OBJECT:
{{
    "decision": "Yes",
    "reasoning": "Based on the data from child agents...",
    "sufficient_materials": true,
    "machine_states": {{"machine1": "operational", "machine2": "maintenance"}},
    "material_availability": {{"material1": 100.5, "material2": 50.0}},
    "tools_used": ["MaterialCalculatingAgent", "EquipmentMonitoringAgent"]
}}

DO NOT include any text before or after the JSON. Output ONLY the JSON object."""
            ),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]).partial(agent_list=agent_list)

    def _list_agents(self, *args, **kwargs) -> str:
        """
        Tool function: returns the list of child-agent names currently registered.
        """
        agents = list(self.connectors.keys())
        return f"Available agents: {', '.join(agents)}"

    def _delegate_task_sync(self, input: str) -> str:
        """
        Synchronous wrapper for the async delegate_task method.
        
        Args:
            input: String in format "agent_name|message|session_id"
        
        Returns:
            The response from the child agent
        """
        try:
            # Parse the input
            parts = input.split("|", 2)
            if len(parts) != 3:
                return "Error: Input must be in format 'agent_name|message|session_id'"
            
            agent_name, message, session_id = parts
            
            # Run the async method
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a new thread to run the async function
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self._delegate_task(agent_name, message, session_id)
                        )
                        return future.result(timeout=self.child_agent_timeout + 5)
                else:
                    return loop.run_until_complete(
                        self._delegate_task(agent_name, message, session_id)
                    )
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(self._delegate_task(agent_name, message, session_id))
                
        except Exception as e:
            logger.error(f"Error in delegate_task_sync: {e}", exc_info=True)
            return f"Error delegating task: {str(e)}"

    async def _delegate_task(self, agent_name: str, message: str, session_id: str) -> str:
        """
        Async method to delegate a task to a child agent with timeout handling.
        
        Args:
            agent_name: Name of the child agent
            message: Message to send
            session_id: Session identifier
        
        Returns:
            The text response from the child agent
        """
        connector = self.connectors.get(agent_name)
        if connector is None:
            return f"Unknown agent '{agent_name}'. Available agents: {', '.join(self.connectors.keys())}"

        try:
            # Add timeout for child agent calls
            child_task = await asyncio.wait_for(
                connector.send_task(message, session_id),
                timeout=self.child_agent_timeout
            )

            # Extract text from the last history entry if available
            if child_task.history and len(child_task.history) > 1:
                response = child_task.history[-1].parts[0].text
                logger.info(f"Response from {agent_name}: {response[:200]}...")
                return response
            return "No response from agent"
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for {agent_name}")
            return f"Timeout: {agent_name} did not respond within {self.child_agent_timeout} seconds"
        except Exception as e:
            logger.error(f"Error calling {agent_name}: {e}", exc_info=True)
            return f"Error calling {agent_name}: {str(e)}"

    async def check_child_agents(self) -> Dict[str, bool]:
        """
        Check if child agents are accessible.
        
        Returns:
            Dictionary mapping agent names to their availability status
        """
        results = {}
        for name, connector in self.connectors.items():
            try:
                # Try a simple health check
                await asyncio.wait_for(
                    connector.send_task("ping", "health-check"),
                    timeout=5.0
                )
                results[name] = True
                logger.info(f"✓ {name} is accessible")
            except Exception as e:
                results[name] = False
                logger.warning(f"✗ {name} is not accessible: {e}")
        return results
    
    async def check_child_agents_safe(self) -> Dict[str, bool]:
        """
        Safely check if child agents are accessible without blocking.
        
        Returns:
            Dictionary mapping agent names to their availability status
        """
        try:
            return await self.check_child_agents()
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            # Return all agents as unknown status
            return {name: False for name in self.connectors}

    def _extract_text_from_output(self, output: Any) -> str:
        """
        Extract text from various LangChain output formats.
        """
        # If output is a string, return it
        if isinstance(output, str):
            return output
        
        # If output is a list (new format)
        if isinstance(output, list):
            for item in output:
                if isinstance(item, dict):
                    if 'text' in item:
                        return item['text']
                    elif 'content' in item:
                        return item['content']
                elif isinstance(item, str):
                    return item
        
        # If output is a dict with 'text' key
        if isinstance(output, dict):
            if 'text' in output:
                return output['text']
            elif 'content' in output:
                return output['content']
            elif 'output' in output:
                # Recursive call for nested output
                return self._extract_text_from_output(output['output'])
        
        # Fallback: convert to string
        return str(output)

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON object from text string.
        """
        # First, try to parse the entire text as JSON
        try:
            data = json.loads(text)
            if isinstance(data, dict) and 'decision' in data:
                return data
        except:
            pass
        
        # Try multiple patterns to extract JSON
        json_patterns = [
            # JSON in code blocks
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            # Raw JSON object (greedy, to get the full object)
            r'(\{[^}]*"decision"[^}]*\}(?:[^}]*\})*)',
            # Simple JSON object
            r'(\{[^}]*\})',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
            for match in matches:
                try:
                    # Clean up the match
                    if isinstance(match, tuple):
                        match = match[0]
                    match = match.strip()
                    
                    # Skip if it's not JSON-like
                    if not match.startswith('{'):
                        continue
                    
                    # Try to parse it
                    data = json.loads(match)
                    
                    # Check if it has the required fields
                    if isinstance(data, dict) and 'decision' in data:
                        logger.info(f"Successfully extracted JSON from text")
                        return data
                        
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug(f"Failed to parse JSON candidate: {e}")
                    continue
        
        return None

    async def invoke(self, query: str, session_id: str = None) -> str:
        """
        Run the agent executor and return a JSON string.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.current_session_id = session_id
        
        try:
            # Run the agent executor synchronously in a thread pool
            loop = asyncio.get_running_loop()
            raw = await loop.run_in_executor(
                None, 
                self.agent_executor.invoke, 
                {"input": query}
            )
            
            logger.info(f"Raw response type: {type(raw)}")
            logger.debug(f"Full raw response: {raw}")
            
            # Extract the output from the response
            if isinstance(raw, dict):
                output = raw.get('output', raw)
            else:
                output = raw
            
            # Extract text from the output (handles various formats)
            text_output = self._extract_text_from_output(output)
            logger.info(f"Extracted text output: {text_output[:500]}...")
            
            # Extract JSON from the text
            json_data = self._extract_json_from_text(text_output)
            
            if json_data:
                try:
                    # Validate with Pydantic
                    parsed = ProductionAssistantResponse(**json_data)
                    result = parsed.model_dump_json()
                    logger.info(f"Successfully created valid response")
                    return result
                except ValidationError as e:
                    logger.error(f"Validation error: {e}")
            else:
                logger.error(f"Could not extract JSON from text output")
            
        except Exception as e:
            logger.error(f"Error in invoke: {e}", exc_info=True)
        
        # Return error response if all else fails
        error_response = ProductionAssistantResponse(
            decision="Error",
            reasoning="Failed to process the request. The orchestrator could not parse the LLM response properly.",
            sufficient_materials=False,
            machine_states={},
            material_availability={},
            tools_used=[]
        )
        return error_response.model_dump_json()

    def __repr__(self) -> str:
        """String representation of the Orchestrator Agent."""
        return f"OrchestratorAgent(model='{self.llm.model}', tools={len(self.tools)}, connectors={list(self.connectors.keys())})"


class OrchestratorTaskManager(InMemoryTaskManager):
    """
    TaskManager wrapper: exposes OrchestratorAgent.invoke() over the
    A2A JSON-RPC /tasks/send endpoint.
    """

    def __init__(self, agent: OrchestratorAgent):
        super().__init__()
        self.agent = agent
        self._health_check_done = False

    async def _startup_health_check(self):
        """Run health check on child agents at startup."""
        if self._health_check_done:
            return
        
        self._health_check_done = True
        logger.info("Running health check on child agents...")
        
        try:
            health_status = await self.agent.check_child_agents_safe()
            
            all_healthy = all(health_status.values())
            if all_healthy:
                logger.info("✓ All child agents are accessible")
            else:
                unavailable = [name for name, status in health_status.items() if not status]
                logger.warning(f"⚠ Some child agents are not accessible: {unavailable}")
                logger.info("The orchestrator will continue, but may fail when trying to contact unavailable agents")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            logger.info("Continuing without health check...")

    def _get_user_text(self, request: SendTaskRequest) -> str:
        """
        Helper: extract the user's raw input text from the request object.
        """
        return request.params.message.parts[0].text

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Called by the A2A server when a new task arrives.
        """
        try:
            logger.info(f"OrchestratorTaskManager received task {request.params.id}")
            
            # Run health check on first request if not done
            if not self._health_check_done:
                await self._startup_health_check()

            # Step 1: save the initial message
            task = await self.upsert_task(request.params)

            # Step 2: run orchestration logic with timeout
            user_text = self._get_user_text(request)
            
            try:
                # Add overall timeout for the entire orchestration
                response_text = await asyncio.wait_for(
                    self.agent.invoke(user_text, request.params.sessionId),
                    timeout=90.0  # 90 second overall timeout
                )
            except asyncio.TimeoutError:
                logger.error("Overall orchestration timeout")
                error_dict = {
                    "decision": "Error",
                    "reasoning": "Request timed out while processing",
                    "sufficient_materials": False,
                    "machine_states": {},
                    "material_availability": {},
                    "tools_used": []
                }
                response_text = json.dumps(error_dict)
            
            # Ensure response_text is a string
            if not isinstance(response_text, str):
                if isinstance(response_text, dict):
                    response_text = json.dumps(response_text)
                else:
                    response_text = str(response_text)
            
            logger.info(f"Final response (first 200 chars): {response_text[:200]}")
            
            # Step 3: wrap the LLM output into a Message
            reply = Message(
                role="agent", 
                parts=[TextPart(text=response_text)]
            )
            
            # Step 4: update task status and history
            async with self.lock:
                task.status = TaskStatus(state=TaskState.COMPLETED)
                task.history.append(reply)

            # Step 5: return structured response
            response = SendTaskResponse(id=request.id, result=task)
            logger.info(f"Returning response for task {request.params.id}")
            return response
            
        except Exception as e:
            logger.error(f"Fatal error in on_send_task: {e}", exc_info=True)
            
            # Create an error task response
            error_dict = {
                "decision": "Error",
                "reasoning": f"Fatal error: {str(e)}",
                "sufficient_materials": False,
                "machine_states": {},
                "material_availability": {},
                "tools_used": []
            }
            
            # Try to return a proper error response
            try:
                task = await self.upsert_task(request.params)
                reply = Message(
                    role="agent",
                    parts=[TextPart(text=json.dumps(error_dict))]
                )
                async with self.lock:
                    task.status = TaskStatus(state=TaskState.FAILED)
                    task.history.append(reply)
                return SendTaskResponse(id=request.id, result=task)
            except:
                # Last resort - raise the error
                raise