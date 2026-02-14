"""
Knowledge Base for RAPID-100 Emergency Call Triage System
Uses ChromaDB vector database for storing and retrieving emergency-related information
"""

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import QueryResult
import pandas as pd
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class EmergencyKnowledgeBase:
    def __init__(self):
        # Initialize ChromaDB cloud client with credentials
        try:
            self.client = chromadb.CloudClient(
                api_key=os.getenv('CHROMADB_API_KEY', 'ck-BmsXgDoCnurtoBXkMD5631XwEBGAXAJyg65rkhnRpeJH'),
                tenant=os.getenv('CHROMADB_TENANT', '15b29fe8-c72a-47fc-b82a-0e25c0a2560c'),
                database=os.getenv('CHROMADB_DATABASE', 'rapid100-ai-dispatch')
            )
        except Exception as e:
            logger.warning(f"Failed to connect to ChromaDB Cloud: {e}. Falling back to persistent client.")
            # Fallback to local persistent client
            self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Initialize sentence transformer model for embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create collections for different types of emergency data
        self.emergency_collection = self.client.get_or_create_collection(
            name="emergency_scenarios",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.procedures_collection = self.client.get_or_create_collection(
            name="emergency_procedures",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.location_collection = self.client.get_or_create_collection(
            name="location_info",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Load initial data
        self._load_initial_data()
    
    def _load_initial_data(self):
        """Load initial emergency data into the knowledge base"""
        try:
            # Load emergency scenarios from the dataset
            dataset_path = "./dataset/emergency_calls_dataset.csv"
            if os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
                
                # Add emergency scenarios to collection
                for idx, row in df.iterrows():
                    scenario_text = f"Emergency: {row['emergency_type']}. Transcript: {row['transcript']}. Severity: {row['severity']}. Location: {row['location']}"
                    
                    embedding = self.embedding_model.encode(scenario_text).tolist()
                    
                    self.emergency_collection.add(
                        documents=[scenario_text],
                        metadatas=[{
                            "emergency_type": row['emergency_type'],
                            "severity": row['severity'],
                            "location": row['location'],
                            "transcript": row['transcript']
                        }],
                        ids=[f"scenario_{idx}"]
                    )
                
                logger.info(f"Loaded {len(df)} emergency scenarios into knowledge base")
            
            # Add some general emergency procedures
            emergency_procedures = [
                {
                    "procedure": "Cardiopulmonary Resuscitation (CPR)",
                    "details": "For unconscious victims who are not breathing normally. Place heel of one hand on center of chest, place other hand on top, interlock fingers, and compress at least 2 inches deep at 100-120 compressions per minute.",
                    "type": "Medical"
                },
                {
                    "procedure": "Fire Evacuation",
                    "details": "Evacuate immediately using nearest safe exit. Do not use elevators. If smoke is present, stay low and cover nose and mouth with cloth. Meet at designated assembly point.",
                    "type": "Fire"
                },
                {
                    "procedure": "Active Shooter",
                    "details": "Run: Evacuate quickly and quietly. Hide: Barricade doors, turn off lights, stay quiet. Fight: As last resort, act with aggression.",
                    "type": "Crime"
                },
                {
                    "procedure": "Car Accident",
                    "details": "Check for injuries, call 911, move vehicles if safe to do so, exchange information, document scene with photos.",
                    "type": "Accident"
                },
                {
                    "procedure": "Natural Disaster",
                    "details": "Follow evacuation orders, go to highest ground if flooding, shelter in place if advised, have emergency kit ready.",
                    "type": "Disaster"
                }
            ]
            
            for idx, proc in enumerate(emergency_procedures):
                procedure_text = f"Procedure: {proc['procedure']}. Details: {proc['details']}. Type: {proc['type']}"
                
                embedding = self.embedding_model.encode(procedure_text).tolist()
                
                self.procedures_collection.add(
                    documents=[procedure_text],
                    metadatas={
                        "procedure": proc['procedure'],
                        "type": proc['type'],
                        "details": proc['details']
                    },
                    ids=[f"procedure_{idx}"]
                )
            
            logger.info("Loaded emergency procedures into knowledge base")
            
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
    
    def add_emergency_scenario(self, transcript: str, emergency_type: str, severity: str, location: str, background_noise: str = "", emotion_intensity: float = 0.0):
        """Add a new emergency scenario to the knowledge base"""
        try:
            scenario_text = f"Emergency: {emergency_type}. Transcript: {transcript}. Severity: {severity}. Location: {location}. Background noise: {background_noise}. Emotion intensity: {emotion_intensity}"
            
            embedding = self.embedding_model.encode(scenario_text).tolist()
            
            doc_id = f"scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.emergency_collection.get())}"
            
            self.emergency_collection.add(
                documents=[scenario_text],
                metadatas=[{
                    "emergency_type": emergency_type,
                    "severity": severity,
                    "location": location,
                    "transcript": transcript,
                    "background_noise": background_noise,
                    "emotion_intensity": emotion_intensity,
                    "timestamp": datetime.now().isoformat()
                }],
                ids=[doc_id]
            )
            
            logger.info(f"Added emergency scenario to knowledge base: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error adding emergency scenario: {e}")
    
    def search_similar_scenarios(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar emergency scenarios to the given query"""
        try:
            embedding = self.embedding_model.encode(query).tolist()
            
            results = self.emergency_collection.query(
                query_embeddings=[embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching similar scenarios: {e}")
            return []
    
    def search_procedures(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search for relevant emergency procedures"""
        try:
            embedding = self.embedding_model.encode(query).tolist()
            
            results = self.procedures_collection.query(
                query_embeddings=[embedding],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "procedure": results['metadatas'][0][i]['procedure'],
                    "details": results['metadatas'][0][i]['details'],
                    "type": results['metadatas'][0][i]['type'],
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching procedures: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get statistics about the knowledge base"""
        try:
            emergency_count = len(self.emergency_collection.get())
            procedures_count = len(self.procedures_collection.get())
            
            return {
                "emergency_scenarios": emergency_count,
                "procedures": procedures_count,
                "collections": 3  # emergency, procedures, location
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"emergency_scenarios": 0, "procedures": 0, "collections": 0}


# Global instance of the knowledge base
kb_instance = None

def get_knowledge_base():
    """Get or create the knowledge base instance"""
    global kb_instance
    if kb_instance is None:
        kb_instance = EmergencyKnowledgeBase()
    return kb_instance