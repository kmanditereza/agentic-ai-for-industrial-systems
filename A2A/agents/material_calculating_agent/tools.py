import asyncio
from agents.material_calculating_agent.database_data_access import get_product_details
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


# create a tool for getting product details and mapping it to the function
get_product_details_tool = Tool(
    name="get_product_details",
    func=get_product_details,  # Using the function directly, NOT calling it
    description="Get the recipe details for a specific product including material requirements. Input should be the product name as a string."
)





