"""
tools_enhanced.py
Enhanced tools module that combines existing OPC UA/Database tools with RAG capabilities
"""

import asyncio
from batch_plant_functions import get_material_availability, get_machine_states
from batch_plant_storage import get_product_details
from langchain.tools import Tool

# Import the RAG module
from maintenance_rag import MaintenanceRAG, create_maintenance_tools

# ============================================================================
# EXISTING TOOLS (from current implementation)
# ============================================================================

# Create synchronous wrappers for async functions
def material_availability_sync(*args, **kwargs):
    """Synchronous wrapper for async get_material_availability function"""
    return asyncio.run(get_material_availability())

def machine_states_sync(*args, **kwargs):
    """Synchronous wrapper for async get_machine_states function"""
    return asyncio.run(get_machine_states())

# Original tools
get_material_availability_tool = Tool(
    name="get_material_availability",
    func=material_availability_sync,
    description="Return the current level (in litres) of raw-material tanks 1-3 by reading their OPC-UA nodes on the batch-plant server."
)

get_machine_states_tool = Tool(
    name="get_machine_states",
    func=machine_states_sync,
    description="Return the current states of machines in the batch plant by reading their OPC-UA nodes."
)

get_product_details_tool = Tool(
    name="get_product_details",
    func=get_product_details,
    description="Get the recipe details for a specific product including material requirements. Input should be the product name as a string."
)

# ============================================================================
# INITIALIZE RAG SYSTEM
# ============================================================================

# Initialize the RAG system (this will be done once when the module is imported)
print("Initializing Maintenance RAG System...")
maintenance_rag = MaintenanceRAG(
    docs_path="./maintenance_docs",
    persist_directory="./chroma_db",
    embedding_model="local"  # Change to "openai" if using OpenAI embeddings
)

# Create RAG tools
rag_tools = create_maintenance_tools(maintenance_rag)

# ============================================================================
# COMBINE ALL TOOLS
# ============================================================================

# List of all available tools
ALL_TOOLS = [
    # Original real-time data tools
    get_material_availability_tool,
    get_machine_states_tool,
    get_product_details_tool,
    
    # New RAG-powered maintenance tools
    *rag_tools  # Unpacks the list of RAG tools
]

# For backward compatibility, also export individual tools
check_maintenance_schedule_tool = rag_tools[0]
check_calibration_status_tool = rag_tools[1]
check_equipment_reliability_tool = rag_tools[2]
get_maintenance_context_tool = rag_tools[3]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_tools_for_production_check():
    """
    Get the essential tools for production feasibility checking
    """
    return [
        get_product_details_tool,
        get_material_availability_tool,
        get_machine_states_tool,
        check_maintenance_schedule_tool,
        check_calibration_status_tool,
        check_equipment_reliability_tool
    ]

def get_all_tools():
    """
    Get all available tools including RAG
    """
    return ALL_TOOLS

def refresh_rag_index():
    """
    Refresh the RAG index by re-loading all documents
    Useful if documents have been updated
    """
    maintenance_rag.clear_database()
    print("RAG index refreshed successfully")

def search_maintenance_docs(query: str, num_results: int = 3):
    """
    Direct semantic search in maintenance documents
    Useful for testing and debugging
    """
    results = maintenance_rag.semantic_search(query, k=num_results)
    return [
        {
            "content": doc.page_content[:500],
            "source": doc.metadata.get('filename', 'Unknown'),
            "section": doc.metadata.get('section', 'General')
        }
        for doc in results
    ]

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing Enhanced Tools with RAG Integration")
    print("="*60)
    
    # Test original tools
    print("\n1. Testing Original Tools:")
    print("-" * 40)
    
    print("Material Availability:")
    print(material_availability_sync())
    
    print("\nMachine States:")
    print(machine_states_sync())
    
    print("\nProduct Details for Product A:")
    print(get_product_details("Product A"))
    
    # Test RAG tools
    print("\n2. Testing RAG Tools:")
    print("-" * 40)
    
    print("Maintenance Schedule Check:")
    result = check_maintenance_schedule_tool.func("Product A, 2025-01-23")
    print(result)
    
    print("\nCalibration Status Check:")
    result = check_calibration_status_tool.func("Product A, 2025-01-23")
    print(result)
    
    print("\nEquipment Reliability Check:")
    result = check_equipment_reliability_tool.func("")
    print(result)
    
    # Test semantic search
    print("\n3. Testing Semantic Search:")
    print("-" * 40)
    results = search_maintenance_docs("vibration limits reactor")
    for r in results:
        print(f"Source: {r['source']}")
        print(f"Section: {r['section']}")
        print(f"Content: {r['content'][:200]}...")
        print()
    
    print("\n" + "="*60)
    print("All Tools Testing Complete!")
    print(f"Total tools available: {len(ALL_TOOLS)}")
    print("="*60)