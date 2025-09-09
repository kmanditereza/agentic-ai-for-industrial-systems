import asyncio
from agents.equipment_monitoring_agent.opcua_data_access import get_material_availability, get_machine_states
from langchain.tools import Tool



""" 
Our async functions (get_material_availability, get_machine_states) cannot be used directly with LangChain's Tool class, which expects synchronous functions.
Create synchronous wrapper functions that use asyncio.run() to execute the async functions

The issue is that LLMs sometimes try to be "helpful" by passing arguments to functions even when they don't need them. By adding *args, **kwargs to the wrapper functions, we allow them to accept any arguments but simply ignore them.
This is a common pattern when working with LangChain tools because:

The LLM might interpret the function description and decide to pass arguments
The actual OPC UA functions don't need any arguments (they read fixed node IDs)
We need to handle this gracefully

The modified wrapper functions will now accept any arguments the agent tries to pass but will ignore them and call the underlying functions without any arguments, which is what we want.
"""

# Create synchronous wrappers for async functions
def material_availability_sync(*args, **kwargs):
    """Synchronous wrapper for async get_material_availability function"""
    # Ignore any arguments passed by the agent
    return asyncio.run(get_material_availability())

def machine_states_sync(*args, **kwargs):
    """Synchronous wrapper for async get_machine_states function"""
    # Ignore any arguments passed by the agent
    return asyncio.run(get_machine_states())


# create a tool for getting material availability and mapping it to the function
get_material_availability_tool = Tool(
    name="get_material_availability",
    func=material_availability_sync,
    description="Return the current level (in litres) of raw-material tanks 1-3 by reading their OPC-UA nodes on the batch-plant server."
)

# create a tool for getting machine states and mapping it to the function
get_machine_states_tool = Tool(
    name="get_machine_states",
    func=machine_states_sync,
    description="Return the current states of machines in the batch plant by reading their OPC-UA nodes."
)






