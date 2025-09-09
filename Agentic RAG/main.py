"""
main_enhanced.py
Enhanced main agent that uses RAG for maintenance-aware production decisions
"""

import asyncio
import json
from typing import Dict, List, Optional
import dotenv
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_ollama import ChatOllama

# Import enhanced tools with RAG
from tools import get_all_tools, get_tools_for_production_check

load_dotenv()

class ProductionAssistantResponse(BaseModel):
    """Enhanced response model with maintenance considerations"""
    decision: str  # YES, NO, or CONDITIONAL
    reasoning: str
    sufficient_materials: bool
    machine_states: Dict[str, str]
    material_availability: Dict[str, float]
    maintenance_conflicts: Optional[List[Dict]] = []
    calibration_issues: Optional[List[Dict]] = []
    reliability_concerns: Optional[List[Dict]] = []
    recommendations: Optional[List[str]] = []
    tools_used: List[str]

# Initialize LLM (you can switch between these)
#llm_openai = ChatOpenAI(model="gpt-4o")
llm_anthropic = ChatAnthropic(model="claude-3-5-sonnet-20241022")
#llm_mistral = ChatOllama(model="mistral", temperature=0)

parser = PydanticOutputParser(pydantic_object=ProductionAssistantResponse)

# Enhanced prompt with RAG instructions
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an Advanced Batch Plant Production Assistant with access to both real-time data and maintenance documentation.

Your task is to provide a COMPREHENSIVE production feasibility assessment by analyzing:
1. Material availability
2. Machine operational states
3. Maintenance schedules and conflicts
4. Calibration status of critical instruments
5. Equipment reliability and spare parts availability

CRITICAL DECISION PROCESS:
1. First, get the product recipe to understand material requirements
2. Check current material levels in tanks
3. Verify all machines are operational (not in fault/maintenance state)
4. Check maintenance schedules for any conflicts during production window
5. Verify calibration status for critical instruments
6. Assess equipment reliability and spare parts availability
7. Calculate if materials are sufficient for requested batches

PRODUCTION RULES:
- Product A: Cannot be produced within 24 hours after reactor maintenance
- Product A: Requires ALL instruments to be within calibration
- ALL Products: Require equipment health scores above minimum thresholds
- ALL Products: Cannot proceed if critical spare parts are at zero

DECISION CATEGORIES:
- YES: All checks pass, production can proceed safely
- NO: Critical issues prevent production (list specific blockers)
- CONDITIONAL: Production possible with constraints or after specific actions

Always provide:
- Specific reasons for your decision
- Quantitative data (material calculations, dates, percentages)
- Clear recommendations for addressing any issues
- Risk assessment if proceeding with warnings

IMPORTANT: Your final response must be ONLY valid JSON in the specified format.

{format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

# Get all tools including RAG
tools = get_all_tools()

# Create agent with enhanced tools
agent = create_tool_calling_agent(llm=llm_anthropic, prompt=prompt, tools=tools)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,  # Set to True to see the agent's thinking process
    max_iterations=10,  # Increase for complex queries requiring multiple tool calls
    handle_parsing_errors=True
)

def extract_json_from_response(response):
    """Extract JSON from various response formats"""
    if isinstance(response, dict) and 'output' in response:
        output = response['output']
        
        if isinstance(output, list):
            for item in output:
                if isinstance(item, dict) and 'text' in item:
                    text = item['text']
                    try:
                        import re
                        json_match = re.search(r'\{.*\}', text, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                    except:
                        pass
        
        elif isinstance(output, str):
            try:
                return json.loads(output)
            except:
                import re
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
    
    if isinstance(response, dict) and 'decision' in response:
        return response
    
    raise ValueError("Could not extract JSON from response")

def print_production_assessment(response: ProductionAssistantResponse):
    """Pretty print the production assessment"""
    print("\n" + "="*70)
    print("🏭 PRODUCTION FEASIBILITY ASSESSMENT")
    print("="*70)
    
    # Decision with color coding
    decision_emoji = {
        "YES": "✅",
        "NO": "❌",
        "CONDITIONAL": "⚠️"
    }
    print(f"\n{decision_emoji.get(response.decision, '📊')} DECISION: {response.decision}")
    
    # Reasoning
    print(f"\n📋 REASONING:")
    print(f"{response.reasoning}")
    
    # Material Assessment
    print(f"\n📦 MATERIAL ASSESSMENT:")
    print(f"   Sufficient Materials: {'✅ Yes' if response.sufficient_materials else '❌ No'}")
    for tank, level in response.material_availability.items():
        print(f"   • {tank}: {level:,.2f} units")
    
    # Machine States
    print(f"\n🔧 MACHINE STATES:")
    for machine, state in response.machine_states.items():
        status_icon = "🟢" if state.lower() in ["idle", "running"] else "🔴"
        print(f"   {status_icon} {machine}: {state}")
    
    # Maintenance Conflicts
    if response.maintenance_conflicts:
        print(f"\n🔧 MAINTENANCE CONFLICTS:")
        for conflict in response.maintenance_conflicts:
            print(f"   ⚠️ {conflict}")
    
    # Calibration Issues
    if response.calibration_issues:
        print(f"\n📏 CALIBRATION ISSUES:")
        for issue in response.calibration_issues:
            print(f"   ⚠️ {issue}")
    
    # Reliability Concerns
    if response.reliability_concerns:
        print(f"\n⚡ RELIABILITY CONCERNS:")
        for concern in response.reliability_concerns:
            print(f"   ⚠️ {concern}")
    
    # Recommendations
    if response.recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in response.recommendations:
            print(f"   → {rec}")
    
    # Tools Used
    print(f"\n🛠️ ANALYSIS TOOLS USED:")
    for tool in response.tools_used:
        print(f"   • {tool}")
    
    print("\n" + "="*70)

def run_production_check(query: str = None):
    """
    Run a production feasibility check
    
    Args:
        query: Optional query string. If not provided, will prompt user.
    """
    if not query:
        print("\n" + "="*70)
        print("🏭 BATCH PLANT PRODUCTION ASSISTANT (with RAG)")
        print("="*70)
        print("\nThis assistant checks real-time data AND maintenance documentation")
        print("to provide comprehensive production feasibility assessments.\n")
        
        print("Example queries:")
        print("  - Can we produce 50 batches of Product A starting tomorrow?")
        print("  - Is it safe to start Product A production on January 23?")
        print("  - Check if we can run 30 batches of Product A today")
        print()
        
        query = input("Enter your production request: ")
    
    try:
        print("\n🔍 Analyzing production feasibility...")
        print("(Checking real-time data, maintenance schedules, calibrations, and reliability...)\n")
        
        # Run the agent
        raw_response = agent_executor.invoke({"query": query})
        
        # Extract JSON from response
        json_data = extract_json_from_response(raw_response)
        
        # Parse with Pydantic
        structured_response = ProductionAssistantResponse(**json_data)
        
        # Pretty print the response
        print_production_assessment(structured_response)
        
        return structured_response
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        print("\nTrying to extract partial information...")
        
        if 'raw_response' in locals():
            print("\nRaw Response:")
            print(json.dumps(raw_response, indent=2))
        
        return None

def run_test_scenarios():
    """Run predefined test scenarios to demonstrate GO/NO-GO decisions"""
    
    scenarios = [
        {
            "name": "Scenario 1: Normal Production",
            "query": "Can we produce 50 batches of Product A starting January 26, 2025?",
            "expected": "Should be YES if no maintenance conflicts"
        },
        {
            "name": "Scenario 2: Maintenance Conflict",
            "query": "Can we produce 50 batches of Product A starting January 23, 2025?",
            "expected": "Should be NO due to reactor maintenance"
        },
        {
            "name": "Scenario 3: Calibration Check",
            "query": "Can we produce 30 batches of Product A starting January 24, 2025?",
            "expected": "Depends on calibration expiry dates"
        }
    ]
    
    print("\n" + "="*70)
    print("🧪 RUNNING TEST SCENARIOS")
    print("="*70)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- {scenario['name']} ---")
        print(f"Query: {scenario['query']}")
        print(f"Expected: {scenario['expected']}")
        print()
        
        result = run_production_check(scenario['query'])
        
        if result:
            print(f"\nResult: {result.decision}")
        
        if i < len(scenarios):
            input("\nPress Enter to continue to next scenario...")

if __name__ == "__main__":
    # You can either run interactive mode or test scenarios
    
    # Option 1: Interactive mode
    run_production_check()
    
    # Option 2: Run test scenarios (uncomment to use)
    # run_test_scenarios()
    
    # Option 3: Direct query (uncomment and modify as needed)
    # run_production_check("Can we produce 50 batches of Product A starting tomorrow?")