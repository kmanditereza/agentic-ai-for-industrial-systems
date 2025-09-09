import asyncio
import json
from typing import Dict, List
import anthropic
import dotenv
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import get_material_availability_tool, get_machine_states_tool, get_product_details_tool
from langchain_ollama import ChatOllama


load_dotenv()

class ProductionAssistantResponse(BaseModel):
    decision: str
    reasoning: str
    sufficient_materials: bool
    machine_states: Dict[str, str]
    material_availability: Dict[str, float]
    tools_used: List[str]


#llm_openai = ChatOpenAI(model="gpt-4o")
#llm_mistral = ChatOllama(model="mistral")
llm_anthropic = ChatAnthropic(model="claude-3-5-sonnet-20241022")
parser = PydanticOutputParser(pydantic_object=ProductionAssistantResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
           You are a Batch Plant Production Assistant. Your task is to analyze whether the plant can produce a specified number of batches for a given product.

            To make this determination, you need to:
            1. First get the product recipe details to understand material requirements
            2. Check current material availability in the tanks
            3. Verify machine states (all must be operational - not in Fault state)
            4. Calculate if there are sufficient materials for the requested batches
            5. Provide a clear decision with reasoning

            Always be specific about:
            - Which materials are sufficient/insufficient
            - Which machines are operational/faulty
            - The exact calculation of material requirements vs availability

            IMPORTANT: Your final response must be ONLY valid JSON in the specified format. Do not include any text before or after the JSON.
            
            {format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

tools = [get_material_availability_tool, get_machine_states_tool, get_product_details_tool]

# Create agent without output parser to handle manually
agent = create_tool_calling_agent(llm=llm_anthropic, prompt=prompt, tools=tools)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)


def extract_json_from_response(response):
    """Extract JSON from various response formats"""
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
                        import re
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
                import re
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
    
    # If response is already a dict that might be the parsed response
    if isinstance(response, dict) and 'decision' in response:
        return response
    
    raise ValueError("Could not extract JSON from response")



if __name__ == "__main__":
    query = input("What product and number of batches do you want to produce? ")
    
    try:
        # Run the agent
        raw_response = agent_executor.invoke({"query": query})
        
        # Extract JSON from response
        json_data = extract_json_from_response(raw_response)
        
        # Parse with Pydantic
        structured_response = ProductionAssistantResponse(**json_data)
        
        # Pretty print the response
        print("\n" + "="*50)
        print("PRODUCTION ASSESSMENT RESULTS")
        print("="*50)
        print(f"\n📊 DECISION: {structured_response.decision}")
        print(f"\n📝 REASONING:\n{structured_response.reasoning}")
        print(f"\n✅ Sufficient Materials: {structured_response.sufficient_materials}")
        
        print(f"\n🏭 MACHINE STATES:")
        for machine, state in structured_response.machine_states.items():
            status_icon = "🟢" if state not in ["fault", "error"] else "🔴"
            print(f"   {status_icon} {machine}: {state}")
        
        print(f"\n🧪 MATERIAL AVAILABILITY:")
        for tank, level in structured_response.material_availability.items():
            print(f"   • {tank}: {level:,.2f} L")
        
        print(f"\n🔧 Tools Used: {', '.join(structured_response.tools_used)}")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nRaw Response:")
        print(json.dumps(raw_response, indent=2))