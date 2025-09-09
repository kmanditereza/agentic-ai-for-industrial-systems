"""
maintenance_rag.py
RAG (Retrieval-Augmented Generation) module for maintenance document analysis
Uses Chroma as the vector database for semantic search
"""

import os
import re
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

# Chroma and LangChain imports
from langchain.text_splitter import MarkdownTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.tools import Tool

# For better parsing of specific document sections
from typing import Union


class MaintenanceRAG:
    """
    RAG system for maintenance documentation using Chroma vector database
    """
    
    def __init__(
        self, 
        docs_path: str = "./maintenance_docs",
        persist_directory: str = "./chroma_db",
        embedding_model: str = "local",  # "local" for Ollama or "openai"
        collection_name: str = "maintenance_docs"
    ):
        """
        Initialize the RAG system with Chroma
        
        Args:
            docs_path: Path to maintenance documents directory
            persist_directory: Path to persist Chroma database
            embedding_model: Which embedding model to use ("local" or "openai")
            collection_name: Name for the Chroma collection
        """
        self.docs_path = docs_path
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize embeddings based on choice
        if embedding_model == "local":
            # Using Ollama with local model
            self.embeddings = OllamaEmbeddings(model="mxbai-embed-large")  # or "llama3.1:8b" - use same model as your LLM
        else:
            # Using OpenAI embeddings
            self.embeddings = OpenAIEmbeddings()
        
        # Initialize or load vector store
        self.vectorstore = None
        self.setup_vectorstore()
    
    def setup_vectorstore(self):
        """
        Set up Chroma vector store - either load existing or create new
        """
        # Check if database already exists
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            print(f"Loading existing Chroma database from {self.persist_directory}")
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"Loaded {self.vectorstore._collection.count()} documents from existing database")
        else:
            print(f"Creating new Chroma database at {self.persist_directory}")
            self.load_and_index_documents()
    
    def load_and_index_documents(self):
        """
        Load documents from directory and create Chroma index
        """
        # Ensure docs directory exists
        if not os.path.exists(self.docs_path):
            print(f"Warning: {self.docs_path} does not exist. Creating empty vector store.")
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            return
        
        # Load all markdown files
        loader = DirectoryLoader(
            self.docs_path,
            glob="*.md",
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )
        
        try:
            documents = loader.load()
            print(f"Loaded {len(documents)} documents from {self.docs_path}")
            
            # Process each document to add metadata
            for doc in documents:
                # Extract document type from filename
                filename = os.path.basename(doc.metadata.get('source', ''))
                doc.metadata['doc_type'] = self._classify_document(filename)
                doc.metadata['filename'] = filename
            
            # Split documents into chunks
            text_splitter = MarkdownTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            
            splits = text_splitter.split_documents(documents)
            print(f"Split into {len(splits)} chunks")
            
            # Add additional metadata to chunks
            for i, split in enumerate(splits):
                split.metadata['chunk_id'] = i
                # Extract section headers if present
                lines = split.page_content.split('\n')
                for line in lines[:3]:  # Check first 3 lines
                    if line.startswith('#'):
                        split.metadata['section'] = line.strip('#').strip()
                        break
            
            # Create Chroma vector store
            self.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                collection_name=self.collection_name,
                persist_directory=self.persist_directory
            )
            
            print(f"Successfully indexed {len(splits)} document chunks in Chroma")
            
        except Exception as e:
            print(f"Error loading documents: {e}")
            # Create empty vector store as fallback
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
    
    def _classify_document(self, filename: str) -> str:
        """
        Classify document type based on filename
        """
        filename_lower = filename.lower()
        if 'schedule' in filename_lower or 'pm' in filename_lower:
            return 'maintenance_schedule'
        elif 'calibration' in filename_lower or 'cert' in filename_lower:
            return 'calibration'
        elif 'report' in filename_lower or 'log' in filename_lower:
            return 'maintenance_log'
        else:
            return 'general'
    
    def semantic_search(self, query: str, k: int = 4, filter_dict: Optional[Dict] = None) -> List[Document]:
        """
        Perform semantic search on the vector database
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of relevant documents
        """
        if not self.vectorstore:
            return []
        
        if filter_dict:
            return self.vectorstore.similarity_search(query, k=k, filter=filter_dict)
        else:
            return self.vectorstore.similarity_search(query, k=k)
    
    def check_maintenance_schedule(self, product_name: str = "Product A", start_date: str = None) -> Dict[str, Any]:
        """
        Check if there are any maintenance conflicts for production
        
        Args:
            product_name: Name of the product to produce
            start_date: Start date for production (YYYY-MM-DD format)
            
        Returns:
            Dictionary with conflicts, warnings, and decision
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        # Convert start_date string to datetime
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except:
            start_dt = datetime.now()
        
        # Build search query
        query = f"""
        maintenance schedule preventive PM {product_name}
        reactor mixer filler scheduled maintenance
        equipment health score threshold
        {start_date} {start_dt.strftime('%B %d')}
        """
        
        # Search for relevant documents
        docs = self.semantic_search(
            query, 
            k=6,
            filter_dict={"doc_type": "maintenance_schedule"}
        )
        
        conflicts = []
        warnings = []
        
        for doc in docs:
            content = doc.page_content
            
            # Check for scheduled maintenance dates
            if "Next Scheduled PM:" in content:
                # Extract maintenance information
                pm_matches = re.findall(
                    r"(MIXER-01|REACTOR-01|FILLER-01).*?Next Scheduled PM:\s*([^,\n]+).*?Duration:\s*(\d+)\s*hours",
                    content,
                    re.DOTALL
                )
                
                for equipment, pm_date_str, duration in pm_matches:
                    # Parse the maintenance date
                    try:
                        # Extract just the date part (January 25, 2025)
                        date_part = re.search(r"([A-Za-z]+ \d+, \d+)", pm_date_str)
                        if date_part:
                            pm_date = datetime.strptime(date_part.group(1), "%B %d, %Y")
                            
                            # Check if maintenance conflicts with production (within 3 days)
                            if start_dt <= pm_date <= start_dt + timedelta(days=3):
                                conflicts.append({
                                    "equipment": equipment,
                                    "maintenance_date": pm_date_str.strip(),
                                    "duration": f"{duration} hours",
                                    "impact": "FULL SHUTDOWN REQUIRED"
                                })
                                
                                # Special rule for Product A and reactor
                                if equipment == "REACTOR-01" and product_name == "Product A":
                                    conflicts.append({
                                        "equipment": equipment,
                                        "issue": "Product A cannot be produced within 24 hours after reactor maintenance",
                                        "earliest_production": (pm_date + timedelta(days=1)).strftime("%B %d, %Y")
                                    })
                    except Exception as e:
                        print(f"Error parsing date: {e}")
            
            # Check equipment health scores
            health_matches = re.findall(
                r"(MIXER-01|REACTOR-01|FILLER-01)\s*\|\s*(\d+)%\s*\|\s*(\d+)%",
                content
            )
            
            for equipment, current_health, min_health in health_matches:
                current = int(current_health)
                minimum = int(min_health)
                
                if current < minimum:
                    conflicts.append({
                        "equipment": equipment,
                        "issue": f"Health score {current}% below minimum {minimum}%",
                        "action": "Maintenance required before production"
                    })
                elif current < minimum + 10:  # Warning threshold
                    warnings.append({
                        "equipment": equipment,
                        "issue": f"Health score {current}% approaching minimum {minimum}%",
                        "action": "Monitor closely"
                    })
        
        return {
            "conflicts": conflicts,
            "warnings": warnings,
            "can_proceed": len(conflicts) == 0,
            "documents_checked": len(docs)
        }
    
    def check_calibration_status(self, product_name: str = "Product A", production_date: str = None) -> Dict[str, Any]:
        """
        Check calibration status for critical instruments
        
        Args:
            product_name: Name of the product
            production_date: Date of production
            
        Returns:
            Dictionary with calibration status
        """
        if not production_date:
            production_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            prod_dt = datetime.strptime(production_date, "%Y-%m-%d")
        except:
            prod_dt = datetime.now()
        
        # Search for calibration documents
        query = f"""
        calibration certificate expires expiry {product_name}
        temperature pressure flow level instruments
        critical instruments validation
        {production_date} {prod_dt.strftime('%B %d')}
        """
        
        docs = self.semantic_search(
            query,
            k=6,
            filter_dict={"doc_type": "calibration"}
        )
        
        expired_instruments = []
        expiring_soon = []
        
        for doc in docs:
            content = doc.page_content
            
            # Find calibration expiry information in tables
            # Look for table rows with dates
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if '|' in line and any(month in line for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                    parts = [p.strip() for p in line.split('|')]
                    
                    if len(parts) >= 5:
                        instrument_id = parts[0]
                        
                        # Skip header rows
                        if 'Instrument' in instrument_id or '---' in instrument_id:
                            continue
                        
                        # Look for expiry date
                        for part in parts:
                            if any(month in part for month in ['Jan', 'Feb', 'Mar']):
                                try:
                                    # Parse date
                                    expiry_date = datetime.strptime(part.strip(), "%b %d, %Y")
                                    
                                    # Check if expired or expiring soon
                                    days_until_expiry = (expiry_date - prod_dt).days
                                    
                                    if days_until_expiry < 0:
                                        expired_instruments.append({
                                            "instrument": instrument_id,
                                            "expired_date": part.strip(),
                                            "days_overdue": abs(days_until_expiry),
                                            "critical_for_product_a": "Product A" in content
                                        })
                                    elif days_until_expiry <= 3:
                                        expiring_soon.append({
                                            "instrument": instrument_id,
                                            "expires": part.strip(),
                                            "days_remaining": days_until_expiry
                                        })
                                    break
                                except:
                                    pass
        
        # Check for Product A specific rules
        product_a_violation = False
        if product_name == "Product A" and expired_instruments:
            product_a_violation = True
        
        return {
            "expired": expired_instruments,
            "expiring_soon": expiring_soon,
            "can_proceed": len(expired_instruments) == 0,
            "product_a_violation": product_a_violation,
            "documents_checked": len(docs)
        }
    
    def check_equipment_reliability(self, check_spares: bool = True) -> Dict[str, Any]:
        """
        Check equipment reliability metrics and spare parts
        
        Args:
            check_spares: Whether to check spare parts inventory
            
        Returns:
            Dictionary with reliability assessment
        """
        query = """
        MTBF reliability vibration failure hours
        spare parts inventory mixer reactor filler
        vibration levels temperature bearing
        recent maintenance emergency repair
        """
        
        docs = self.semantic_search(
            query,
            k=6,
            filter_dict={"doc_type": "maintenance_log"}
        )
        
        reliability_issues = []
        spare_parts_issues = []
        
        for doc in docs:
            content = doc.page_content
            
            # Check vibration levels
            vib_matches = re.findall(r"Vibration levels?:\s*([\d.]+)\s*mm/s", content, re.IGNORECASE)
            for vib_value in vib_matches:
                vibration = float(vib_value)
                if vibration > 7.5:
                    reliability_issues.append({
                        "type": "vibration",
                        "value": f"{vibration} mm/s",
                        "limit": "7.5 mm/s",
                        "severity": "CRITICAL",
                        "equipment": "REACTOR-01"
                    })
                elif vibration > 5.0:
                    reliability_issues.append({
                        "type": "vibration",
                        "value": f"{vibration} mm/s",
                        "warning_level": "5.0 mm/s",
                        "severity": "WARNING",
                        "equipment": "REACTOR-01"
                    })
            
            # Check MTBF values
            mtbf_matches = re.findall(r"(MIXER-01|REACTOR-01|FILLER-01).*?MTBF.*?:\s*(\d+)\s*hours", content, re.DOTALL)
            for equipment, mtbf_hours in mtbf_matches:
                mtbf = int(mtbf_hours)
                if mtbf < 200:
                    reliability_issues.append({
                        "type": "reliability",
                        "equipment": equipment,
                        "MTBF": f"{mtbf} hours",
                        "severity": "HIGH",
                        "recommendation": "Schedule preventive maintenance"
                    })
            
            # Check spare parts if requested
            if check_spares and "Spare Parts Status" in content:
                # Parse spare parts table
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '|' in line and 'Mixer Seals' in line:
                        parts = [p.strip() for p in line.split('|')]
                        if len(parts) >= 3:
                            try:
                                in_stock = int(parts[2])
                                if in_stock == 0:
                                    spare_parts_issues.append({
                                        "item": "Mixer Seals",
                                        "count": 0,
                                        "severity": "CRITICAL",
                                        "impact": "Cannot recover from seal failure"
                                    })
                                elif in_stock <= 1:
                                    spare_parts_issues.append({
                                        "item": "Mixer Seals",
                                        "count": in_stock,
                                        "severity": "WARNING",
                                        "impact": "At minimum stock level"
                                    })
                            except:
                                pass
        
        # Determine overall risk level
        critical_count = len([i for i in reliability_issues if i.get("severity") == "CRITICAL"])
        critical_count += len([i for i in spare_parts_issues if i.get("severity") == "CRITICAL"])
        
        if critical_count > 0:
            risk_level = "HIGH"
        elif len(reliability_issues) + len(spare_parts_issues) > 2:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "reliability_issues": reliability_issues,
            "spare_parts_issues": spare_parts_issues,
            "risk_level": risk_level,
            "can_proceed": critical_count == 0,
            "documents_checked": len(docs)
        }
    
    def get_maintenance_context(self, query: str, k: int = 3) -> str:
        """
        Get relevant maintenance context for a query
        
        Args:
            query: User query
            k: Number of relevant chunks to retrieve
            
        Returns:
            Formatted context string
        """
        docs = self.semantic_search(query, k=k)
        
        if not docs:
            return "No relevant maintenance documentation found."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('filename', 'Unknown')
            section = doc.metadata.get('section', 'General')
            
            context_parts.append(f"""
Document {i}: {source} - {section}
{doc.page_content[:500]}...
""")
        
        return "\n".join(context_parts)
    
    def clear_database(self):
        """
        Clear the Chroma database and re-index documents
        """
        print(f"Clearing Chroma database at {self.persist_directory}")
        
        # Delete the persist directory
        import shutil
        if os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
        
        # Re-initialize
        self.load_and_index_documents()
        print("Database cleared and re-indexed")


# Create tool functions for LangChain integration
def create_maintenance_tools(rag_system: MaintenanceRAG) -> List[Tool]:
    """
    Create LangChain tools from the RAG system
    
    Args:
        rag_system: Initialized MaintenanceRAG instance
        
    Returns:
        List of LangChain Tool objects
    """
    
    def check_maintenance_wrapper(input_str: str) -> str:
        """Wrapper for maintenance schedule checking"""
        # Parse input - expect format like "Product A, 2025-01-23"
        parts = input_str.split(',')
        product = parts[0].strip() if parts else "Product A"
        date = parts[1].strip() if len(parts) > 1 else None
        
        result = rag_system.check_maintenance_schedule(product, date)
        return json.dumps(result, indent=2)
    
    def check_calibration_wrapper(input_str: str) -> str:
        """Wrapper for calibration checking"""
        parts = input_str.split(',')
        product = parts[0].strip() if parts else "Product A"
        date = parts[1].strip() if len(parts) > 1 else None
        
        result = rag_system.check_calibration_status(product, date)
        return json.dumps(result, indent=2)
    
    def check_reliability_wrapper(input_str: str = "") -> str:
        """Wrapper for reliability checking"""
        result = rag_system.check_equipment_reliability(check_spares=True)
        return json.dumps(result, indent=2)
    
    def get_context_wrapper(query: str) -> str:
        """Wrapper for getting maintenance context"""
        return rag_system.get_maintenance_context(query)
    
    # Create tools
    tools = [
        Tool(
            name="check_maintenance_schedule",
            func=check_maintenance_wrapper,
            description="""Check maintenance schedules and equipment health. 
            Input format: 'Product Name, YYYY-MM-DD' (e.g., 'Product A, 2025-01-23').
            Returns conflicts, warnings, and whether production can proceed."""
        ),
        Tool(
            name="check_calibration_status",
            func=check_calibration_wrapper,
            description="""Check calibration status for critical instruments.
            Input format: 'Product Name, YYYY-MM-DD' (e.g., 'Product A, 2025-01-23').
            Returns expired and expiring calibrations."""
        ),
        Tool(
            name="check_equipment_reliability",
            func=check_reliability_wrapper,
            description="""Check equipment reliability metrics and spare parts.
            No input required. Returns reliability issues, spare parts status, and risk level."""
        ),
        Tool(
            name="get_maintenance_context",
            func=get_context_wrapper,
            description="""Search maintenance documents for relevant information.
            Input: Any search query about maintenance, calibration, or equipment.
            Returns relevant document excerpts."""
        )
    ]
    
    return tools


# Example usage and testing
if __name__ == "__main__":
    print("="*60)
    print("Testing Maintenance RAG System with Chroma")
    print("="*60)
    
    # Initialize RAG system
    rag = MaintenanceRAG(
        docs_path="./maintenance_docs",
        persist_directory="./chroma_db",
        embedding_model="local"  # Change to "openai" if using OpenAI
    )
    
    # Test 1: Check maintenance schedule
    print("\n1. Checking maintenance schedule for Product A on August 16, 2025:")
    result = rag.check_maintenance_schedule("Product A", "2025-08-16")
    print(f"Can proceed: {result['can_proceed']}")
    if result['conflicts']:
        print("Conflicts found:")
        for conflict in result['conflicts']:
            print(f"  - {conflict}")
    
    # Test 2: Check calibration status
    print("\n2. Checking calibration status:")
    result = rag.check_calibration_status("Product A", "2025-08-16")
    print(f"Can proceed: {result['can_proceed']}")
    if result['expired']:
        print("Expired calibrations:")
        for item in result['expired']:
            print(f"  - {item['instrument']}: expired {item['expired_date']}")
    
    # Test 3: Check equipment reliability
    print("\n3. Checking equipment reliability:")
    result = rag.check_equipment_reliability()
    print(f"Risk level: {result['risk_level']}")
    print(f"Can proceed: {result['can_proceed']}")
    
    # Test 4: Semantic search
    print("\n4. Testing semantic search:")
    query = "What are the vibration limits for the reactor?"
    docs = rag.semantic_search(query, k=2)
    for doc in docs:
        print(f"Found in {doc.metadata.get('filename', 'Unknown')}:")
        print(f"  {doc.page_content[:200]}...")
    
    # Test 5: Get context for a query
    print("\n5. Getting maintenance context:")
    context = rag.get_maintenance_context("Can we produce Product A tomorrow?")
    print(context[:500] + "...")
    
    print("\n" + "="*60)
    print("RAG System Testing Complete")
    print("="*60)