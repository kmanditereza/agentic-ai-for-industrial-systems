# =============================================================================
# agents/material_calculating_agent/main.py
# =============================================================================
# Purpose:
# This is the main script that starts your Equipment Monitoring Agent A2A server.
# It:
# - Declares the agent’s capabilities and skills
# - Sets up the A2A server with a task manager and agent
# - Starts listening on a specified host and port
#
# This script can be run directly from the command line:
# =============================================================================

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

# Your custom A2A server class
from shared.a2a.server import A2AServer

# Models for describing agent capabilities and metadata
from shared.models.agent import AgentCard, AgentCapabilities, AgentSkill

# Task manager and agent logic
from agents.material_calculating_agent.task_manager import AgentTaskManager
from agents.material_calculating_agent.agent import MaterialCalculatingAgent

# CLI and logging support
import click           # For creating a clean command-line interface
import logging         # For logging errors and info to the console


# -----------------------------------------------------------------------------
# Setup logging to print info to the console
# -----------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Main Entry Function – Configurable via CLI
# -----------------------------------------------------------------------------

@click.command()
@click.option("--host", default="localhost", help="Host to bind the server to")
@click.option("--port", default=40003, help="Port number for the server")
def main(host, port):
    """
    This function sets up everything needed to start the agent server.
    You can run it via: `python -m agents.equipment_monitoring_agent --host 0.0.0.0 --port 12345`
    """

    # Define what this agent can do – in this case, it does NOT support streaming
    capabilities = AgentCapabilities(streaming=False)

    # Define the skill this agent offers (used in directories and UIs)
    skill = AgentSkill(
        id="material-requirements-calculator",   # Unique skill ID
        name="Tool for Providing Material Requirements for Requested Production",     # Human-friendly name
        description="Replies with Material Requirements for Requested Production",    # What the skill does
        tags=["material requirements"],                       # Optional tags for searching
        examples=["What is the total amount of material required to produce five batches of Product A?", "Can I make three batches of Product A. Is it possible?"]  # Example queries
    )

    # Create an agent card describing this agent’s identity and metadata
    agent_card = AgentCard(
        name="MaterialCalculatingAgent",                               # Name of the agent
        description="This agent replies with material requirements for requested production.",  # Description
        url=f"http://{host}:{port}/",                       # The public URL where this agent lives
        version="1.0.0",                                    # Version number
        defaultInputModes=MaterialCalculatingAgent.SUPPORTED_CONTENT_TYPES,  # Input types this agent supports
        defaultOutputModes=MaterialCalculatingAgent.SUPPORTED_CONTENT_TYPES, # Output types it produces
        capabilities=capabilities,                          # Supported features (e.g., streaming)
        skills=[skill]                                      # List of skills it supports
    )

    # Start the A2A server with:
    # - the given host/port
    # - this agent’s metadata
    # - a task manager that runs the TellTimeAgent
    server = A2AServer(
        host=host,
        port=port,
        agent_card=agent_card,
        task_manager=AgentTaskManager(agent=MaterialCalculatingAgent())
    )

    # Start listening for tasks
    server.start()


# -----------------------------------------------------------------------------
# This runs only when executing the script directly via `python -m`
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
