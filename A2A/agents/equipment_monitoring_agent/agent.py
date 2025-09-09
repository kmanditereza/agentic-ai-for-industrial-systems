# =============================================================================
# agents/equipment_monitoring_agent/agent.py
# =============================================================================
# This file defines an AI agent for monitoring material availability and equipment operational states in a plant
# It uses Langchain and Claude model to respond to fetch data from opc ua servers and provide responses
# =============================================================================


import asyncio
import json
from typing import Dict, List, Any
import anthropic
import dotenv
import re
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from agents.equipment_monitoring_agent.tools import get_material_availability_tool, get_machine_states_tool

load_dotenv()

class ProductionAssistantResponse(BaseModel):
    machine_states: Dict[str, str]
    material_availability: Dict[str, float]
    tools_used: List[str]


class EquipmentMonitoringAgent:
    """
    Batch Plant Monitoring Assistant that checks material availability 
    and operational states of machines in a batch plant.
    """

    # Declare which content types this agent accepts by default
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(
        self, 
        model: str = "claude-3-5-sonnet-20241022",
        verbose: bool = False
    ):
        """
        Initialize the EquipmentAgent with LLM, tools, and prompt template.
        
        Args:
            model: The Anthropic model to use
            verbose: Whether to enable verbose output for the agent executor
        """
        # Initialize the LLM
        self.llm = ChatAnthropic(model=model)
        
        # Initialize the parser
        self.parser = PydanticOutputParser(pydantic_object=ProductionAssistantResponse)
        
        # Create the prompt template
        self.prompt = self._create_prompt_template()
        
        # Set up tools (assuming these are imported or defined elsewhere)
        self.tools = [get_material_availability_tool, get_machine_states_tool]
        
        # Create the agent and executor
        self.agent = create_tool_calling_agent(
            llm=self.llm, 
            prompt=self.prompt, 
            tools=self.tools
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=verbose
        )
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        Create and return the prompt template for the agent.
        
        Returns:
            ChatPromptTemplate: The configured prompt template
        """
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                   You are a Batch Plant Monitoring Assistant. Your task is to respond with the material availability and the operational states of machines in our batch plant.

                    To make this determination, you need to:
                    1. Check current material availability in all the tanks
                    2. Check machine states 

                    Always be specific about:
                    - Which materials are available, in what quantities and in which tanks
                    - Which machines are operational/faulty
                

                    IMPORTANT: Your final response must be ONLY valid JSON in the specified format. Do not include any text before or after the JSON.
                    
                    {format_instructions}
                    """,
                ),
                ("placeholder", "{chat_history}"),
                ("human", "{query}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())
    
    def _extract_json_from_response(self, response: Any) -> Dict[str, Any]:
        """
        Extract JSON from various response formats.
        
        Args:
            response: The raw response from the agent executor
            
        Returns:
            Dict containing the extracted JSON data
            
        Raises:
            ValueError: If JSON cannot be extracted from the response
        """
        # If response is a dict with 'output' key
        if isinstance(response, dict) and 'output' in response:
            output = response['output']
            
            # If output is a list (Anthropic format)
            if isinstance(output, list):
                for item in output:
                    if isinstance(item, dict) and 'text' in item:
                        text = item['text']
                        # Try to find JSON in the text
                        try:
                            # Look for JSON object pattern
                            json_match = re.search(r'\{.*\}', text, re.DOTALL)
                            if json_match:
                                return json.loads(json_match.group())
                        except:
                            pass
            
            # If output is a string
            elif isinstance(output, str):
                try:
                    return json.loads(output)
                except:
                    # Try to extract JSON from string
                    json_match = re.search(r'\{.*\}', output, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
        
        # If response is already a dict that might be the parsed response
        if isinstance(response, dict) and 'decision' in response:
            return response
        
        raise ValueError("Could not extract JSON from response")
    

    async def invoke(self, query: str) -> str:
        """
        Run the (blocking) executor off the event loop and return a JSON string.
        """
        loop = asyncio.get_running_loop()
        raw = await loop.run_in_executor(None, self.agent_executor.invoke, {"query": query})

        # Try to extract structured JSON from the model output
        try:
            data = self._extract_json_from_response(raw)   # expect dict
        except Exception:
            return str(raw)

        # Optional: validate, but always return primitives
        try:
            parsed = ProductionAssistantResponse(**data)
            return parsed.model_dump_json()                # <- STRING
        except ValidationError:
            try:
                return json.dumps(data)                    # dict -> STRING
            except Exception:
                return str(raw)
    
    def __repr__(self) -> str:
        """String representation of the EquipmentMonitoringAgent."""
        return f"EquipmentMonitoringAgent(model='{self.llm.model}', tools={len(self.tools)})"


