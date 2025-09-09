"""
batch_plant_functions.py
OPC UA client implementation for batch plant monitoring
"""

import asyncio
import json
from enum import IntEnum
from typing import Dict, Any
from asyncua import Client
from asyncua.ua import NodeId

# Configuration
SERVER_URL = "opc.tcp://desktop-fjjsr46:26543/BatchPlantServer"
        
TANK1_LEVEL_NODE_ID = "ns=2;i=328"
TANK2_LEVEL_NODE_ID = "ns=2;i=352"
TANK3_LEVEL_NODE_ID = "ns=2;i=376"
        
MIXER_STATE_NODE_ID = "ns=3;s=MixerState"
REACTOR_STATE_NODE_ID = "ns=3;s=Reactor1State"
FILLER_STATE_NODE_ID = "ns=3;s=Filler1State"

class MachineState(IntEnum):
    """Enum mapping for machine states"""
    DISABLED = 0
    IDLE = 1
    RUNNING = 2
    STARVED = 3
    BLOCKED = 4
    PLANNED_DOWNTIME = 5
    UNPLANNED_DOWNTIME = 6
    OTHER = 7


class OPCUABatchPlantClient:
    """OPC UA client for batch plant operations"""
    
    def __init__(self, server_url: str = None):
        """
        Initialize the OPC UA client
        
        Args:
            server_url: URL of the OPC UA server (e.g., "opc.tcp://localhost:4840")
        """
        self.server_url = SERVER_URL
        self.client = None
    
    async def connect(self):
        """Establish anonymous connection to OPC UA server"""
        self.client = Client(self.server_url)
        # Anonymous connection - no username/password
        await self.client.connect()
    
    async def disconnect(self):
        """Disconnect from OPC UA server"""
        if self.client:
            await self.client.disconnect()
    
    async def get_material_availability(self) -> Dict[str, float]:
        """
        Get material levels from three tanks
        
        Args:
            tank1_node_id: Node ID for tank 1 material level
            tank2_node_id: Node ID for tank 2 material level
            tank3_node_id: Node ID for tank 3 material level
            
        Returns:
            JSON object with tank levels
        """
        try:
            # Create node objects
            tank1_node = self.client.get_node(TANK1_LEVEL_NODE_ID)
            tank2_node = self.client.get_node(TANK2_LEVEL_NODE_ID)
            tank3_node = self.client.get_node(TANK3_LEVEL_NODE_ID)
            
            # Read values
            tank1_level = await tank1_node.read_value()
            tank2_level = await tank2_node.read_value()
            tank3_level = await tank3_node.read_value()
            
            # Create result dictionary
            result = {
                "tank1_material_level": float(tank1_level),
                "tank2_material_level": float(tank2_level),
                "tank3_material_level": float(tank3_level)
            }
            
            return result
            
        except Exception as e:
            print(f"Error reading material levels: {e}")
            raise
    
    async def get_machine_states(self) -> Dict[str, str]:
        """
        Get machine states and convert integer values to string states
        
        Args:
            mixer_node_id: Node ID for mixer state
            reactor_node_id: Node ID for reactor state
            filler_node_id: Node ID for filler state
            
        Returns:
            JSON object with machine states as strings
        """
        try:
            # Create node objects
            mixer_node = self.client.get_node(MIXER_STATE_NODE_ID)
            reactor_node = self.client.get_node(REACTOR_STATE_NODE_ID)
            filler_node = self.client.get_node(FILLER_STATE_NODE_ID)
            
            # Read values (integers)
            mixer_state_int = await mixer_node.read_value()
            reactor_state_int = await reactor_node.read_value()
            filler_state_int = await filler_node.read_value()
            
            # Convert integers to state strings
            result = {
                "mixer_state": self._int_to_state_string(mixer_state_int),
                "reactor_state": self._int_to_state_string(reactor_state_int),
                "filler_state": self._int_to_state_string(filler_state_int)
            }
            
            return result
            
        except Exception as e:
            print(f"Error reading machine states: {e}")
            raise
    
    def _int_to_state_string(self, state_int: int) -> str:
        """
        Convert integer state to string representation
        
        Args:
            state_int: Integer state value from OPC UA server
            
        Returns:
            String representation of the state
        """
        try:
            state = MachineState(state_int)
            return state.name.lower()
        except ValueError:
            return f"unknown_state_{state_int}"


# Standalone functions for direct use
async def get_material_availability() -> str:
    """
    Standalone function to get material availability
    
    Returns:
        JSON string with tank levels
    """
    client = OPCUABatchPlantClient()
    try:
        await client.connect()
        result = await client.get_material_availability()
        return json.dumps(result, indent=2)
    finally:
        await client.disconnect()


async def get_machine_states() -> str:
    """
    Standalone function to get machine states
    
    Returns:
        JSON string with machine states
    """
    client = OPCUABatchPlantClient()
    try:
        await client.connect()
        result = await client.get_machine_states()
        return json.dumps(result, indent=2)
    finally:
        await client.disconnect()

# Example usage
async def main():
    """Example of how to use the functions with hardcoded configuration"""
    # Get material availability
    print("Material Availability:")
    print(await get_material_availability())
    print()
    
    # Get machine states
    print("Machine States:")
    print(await get_machine_states())


if __name__ == "__main__":
    asyncio.run(main())