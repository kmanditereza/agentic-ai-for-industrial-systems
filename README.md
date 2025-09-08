# 🏭 Building Agentic AI for Industrial Systems

A comprehensive course teaching you how to build production-ready AI agents for industrial automation, from basic implementations to advanced multi-agent architectures.

## 📺 Complete Project

🎥 **[Watch the Full Course: Building Agentic AI for Industrial Systems](https://youtu.be/2W6rmlkL9vI)**

**Instructor**: Kudzai Manditereza  
**Level**: Beginner to Advanced

## 🎯 Overview

Learn step-by-step how to build fully functional agentic AI for industrial systems, from the basics to advanced multi-agent architectures. This project takes you through a complete journey of industrial AI development using a simulated batch plant environment.

### What You'll Build

Throughout this course, you'll create:
- **Industrial AI Agent** connecting to OPC UA servers and databases
- **Edge-deployed AI** with local LLMs
- **RAG-powered systems** for document understanding
- **MCP servers** for standardized tool access
- **Multi-agent ecosystems** with A2A protocol

### The Industrial Environment

A simulated batch plant with:
- 3 storage tanks for raw materials
- Mixer for blending materials
- Reactor for chemical processing
- Filler for packaging products
- OPC UA server exposing real-time data
- TimescaleDB storing recipes

## 📚 Project Structure

### Part 1: Industrial AI Agent from Scratch
**Folder**: `Batch Plant Agent/`

Build your first industrial AI agent that:
- Connects to OPC UA servers for real-time data
- Queries databases for product recipes
- Makes production decisions
- Uses Claude LLM via API

**Key Concepts**:
- Python functions for data access
- LangChain tool wrapping
- Prompt engineering
- Structured outputs with Pydantic

### Part 2: Local LLMs at the Edge
**Implementation**: Modified `main.py` in Batch Plant Agent

Deploy AI locally by:
- Installing Ollama
- Running Mistral 7B locally
- Swapping cloud LLM for local model
- Maintaining full functionality offline

**Key Concepts**:
- Edge computing for industrial AI
- Data privacy and latency benefits
- Resource management
- Model selection criteria

### Part 3: Agentic RAG for Documents
**Folder**: `Agentic RAG/`

Extend your agent to understand:
- Maintenance schedules
- Calibration certificates
- Equipment reports
- Operational constraints

**Key Concepts**:
- Vector embeddings with Ollama
- ChromaDB for vector storage
- Semantic search implementation
- Agentic vs Naive RAG

### Part 4: MCP Server for Tools
**Folder**: `OPC UA MCP/`

Standardize tool access with:
- FastMCP server implementation
- Universal tool exposure
- Framework-agnostic design
- MCP Inspector testing

**Key Concepts**:
- Model Context Protocol
- Server-side primitives (tools, resources, prompts)
- Client-server architecture
- Transport mechanisms (STDIO, HTTP)

### Part 5: Multi-Agent Systems with A2A
**Folder**: `A2A/`

Build a distributed system with:
- Equipment Monitoring Agent
- Material Calculating Agent
- Orchestrator Agent
- A2A protocol implementation

**Key Concepts**:
- Agent-to-Agent communication
- Agent cards and discovery
- Task orchestration
- JSON-RPC 2.0 messaging

## 📋 Prerequisites

### Required Knowledge
- Basic Python programming
- Understanding of industrial systems (helpful but not required)
- Familiarity with APIs and databases

### System Requirements
- Python 3.8+
- 8GB RAM minimum (16GB recommended for local LLMs)
- 20GB free disk space
- Windows/Mac/Linux OS

### Software Dependencies
- PostgreSQL/TimescaleDB
- OPC UA server (simulated or real)
- Git
- Node.js (for MCP Inspector)
- Ollama (for local models)

## 🚀 Course Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/industrial-ai-course.git
cd industrial-ai-course
```

### 2. Environment Configuration
Create `.env` in each project folder:
```env
# API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # Optional

# Database
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# OPC UA
OPC_SERVER_URL=opc.tcp://localhost:26543/BatchPlantServer
```

-- Insert sample data
INSERT INTO products (name) VALUES ('Product A'), ('Product B');
-- Add materials and recipes as needed
```

## 📖 Learning Path

### Build Basic AI Agent (Parts 1-2)
```bash
cd "Batch Plant Agent"
pip install -r requirements.txt
python main.py
```
- Understand OPC UA connectivity
- Learn LangChain tool creation
- Master prompt engineering

Deploy Locally
```bash
# Install Ollama
ollama pull mistral
# Modify main.py for local LLM
python main.py
```
- Configure edge deployment
- Compare cloud vs local performance

### Implement RAG  (Part 3)
```bash
cd "Agentic RAG"
pip install -r requirements.txt
ollama pull mxbai-embed-large
python maintenance_rag.py
python main.py
```
- Build document pipeline
- Implement semantic search
- Integrate with agent

### Create MCP Server (Part 4)
```bash
cd "OPC UA MCP"
uv init
uv pip install -r requirements.txt
uv run batch_plant_functions.py
```
- Understand MCP architecture
- Build reusable tools
- Test with inspector

### Multi-Agent Systems Using A2A (Part 5)
```bash
cd A2A
pip install -r requirements.txt

# Start all agents
python -m agents.equipment_monitoring_agent
python -m agents.material_calculating_agent
python -m agents.orchestrator_agent
python -m app.cmd
```
- Implement A2A protocol
- Create specialized agents
- Build orchestration logic

## 🧪 Testing Your Implementation

### Part 1 Test: Basic Query
```
Query: Can we produce 3 batches of Product A?
Expected: Decision with material calculations
```

### Part 2 Test: Local Deployment
```
Query: Same as Part 1, but offline
Expected: Response from local Mistral model
```

### Part 3 Test: Document Context
```
Query: Can we produce Product A tomorrow?
Expected: Checks maintenance schedules
```

### Part 4 Test: MCP Tools
```
Use MCP Inspector to verify:
- get_material_availability tool
- get_machine_states tool
```

### Part 5 Test: Multi-Agent
```
Query to Orchestrator: Can we produce 4 batches?
Expected: Delegates to specialist agents
```

## 📁 Complete Project Structure

```
industrial-ai-course/
├── Batch Plant Agent/        # Part 1 & 2
│   ├── batch_plant_functions.py
│   ├── batch_plant_storage.py
│   ├── main.py
│   ├── tools.py
│   └── requirements.txt
│
├── Agentic RAG/              # Part 3
│   ├── maintenance_rag.py
│   ├── main.py
│   ├── tools.py
│   ├── maintenance_docs/
│   └── chroma_db/
│
├── OPC UA MCP/               # Part 4
│   ├── batch_plant_functions.py
│   ├── pyproject.toml
│   └── requirements.txt
│
└── A2A/                      # Part 5
    ├── agents/
    │   ├── equipment_monitoring_agent/
    │   ├── material_calculating_agent/
    │   └── orchestrator_agent/
    ├── app/
    ├── shared/
    └── requirements.txt
```

## 🎓 Learning Objectives

By completing this course, you will:

### Technical Skills
- ✅ Build production-ready industrial AI agents
- ✅ Deploy LLMs at the edge
- ✅ Implement RAG pipelines
- ✅ Create standardized tool servers
- ✅ Design multi-agent systems

### Conceptual Understanding
- ✅ Industrial data integration patterns
- ✅ Edge vs cloud deployment tradeoffs
- ✅ Structured vs unstructured data handling
- ✅ Agent communication protocols
- ✅ System architecture principles

## 🚀 Next Steps

After completing the course:

1. **Extend the System**
   - Add predictive maintenance agent
   - Implement quality control agent
   - Build production optimization

2. **Production Deployment**
   - Containerize with Docker
   - Add authentication/authorization
   - Implement monitoring/logging

3. **Advanced Topics**
   - Multi-modal agents (vision + text)
   - Reinforcement learning for optimization
   - Digital twin integration

## 🤝 Community & Support

### Getting Help
- GitHub Issues for bug reports
- Discussions for questions
- YouTube comments for course feedback

### Contributing
1. Fork the repository
2. Create feature branch
3. Submit pull request
4. Share your industrial use cases

## 📚 Additional Resources

### Documentation
- [LangChain Docs](https://python.langchain.com/)
- [A2A Protocol Spec](https://github.com/google/agent-to-agent)
- [MCP Specification](https://modelcontextprotocol.io/)
- [OPC UA Foundation](https://opcfoundation.org/)



## 🙏 Acknowledgments

**Instructor**: Kudzai Manditereza
- YouTube: [Channel Link](https://www.youtube.com/@industry40tvonline)
- LinkedIn: [Profile](https://www.linkedin.com/in/kudzaimanditereza/)

**Special Thanks**:
- Anthropic (Claude LLM)
- Google (A2A Protocol)
- LangChain Team
- Open Source Community



**⭐ If this course helps you, please star the repository!**


