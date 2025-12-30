import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ExperienceManager:
    pass


#     """
#     Akashic Hub: Manages long-term memory of decisions and their consequences.
#     Uses RAG to retrieve similar past market contexts.
#     """
def __init__(self, persist_directory: str = "./data/chroma_experiences"):
    pass
    self.persist_directory = persist_directory
    os.makedirs(persist_directory, exist_ok=True)


# Lazy load chromadb
import chromadb
from chromadb.utils import embedding_functions

self.client = chromadb.PersistentClient(path=persist_directory)
# Initialize Embeddings
self.embeddings = self._init_embeddings()
# Fallback to default Chroma embedding function for local ops if Gemini fails
self.default_ef = embedding_functions.DefaultEmbeddingFunction()
# try:
# We must specify the embedding function during collection creation/get
# if we want Chroma to handle it automatically for us.
ef = self.default_ef if not self.embeddings else None
self.collection = self.client.get_collection(
    name="decision_history", embedding_function=ef
)
#             logger.info("Loaded existing decision history collection")
#         except:
#             ef = self.default_ef if not self.embeddings else None
#             self.collection = self.client.create_collection(
#                 name="decision_history",
#                 metadata={"description": "Memory of past market contexts and decisions"},
#                 embedding_function=ef,
#             )
#             logger.info("Created new decision history collection")
#     def _init_embeddings(self):
#         pass
#         """
#         Init Embeddings.
#             Returns:
#     pass
#                 Description of return value
#                         try:
#     pass
#                             api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
#             if not api_key:
#     pass
#                 return None
from langchain_google_genai import GoogleGenerativeAIEmbeddings


# return GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
# except Exception as e:
#             logger.error(f"Failed to init embeddings for ExperienceManager: {e}")
#             return None
# """
def record_decision(self, decision_id: str, context: str, metadata: Dict[str, Any]):
    pass


#         """
#         Stores a new decision context into the records.
#                 try:
#     pass
#                     # Ensure metadata is serializable for Chroma
#             serializable_metadata = {}
#             for k, v in metadata.items():
#     pass
#                 if isinstance(v, (str, int, float, bool)):
#     pass
#                     serializable_metadata[k] = v
#                 else:
#     pass
#                     serializable_metadata[k] = str(v)
#                 params = {"ids": [decision_id], "documents": [context], "metadatas": [serializable_metadata]}
# # If we have custom embeddings, we provide them.
# # Otherwise, Chroma will use the default_ef assigned during collection creation.
#             if self.embeddings:
#     pass
#                 params["embeddings"] = [self.embeddings.embed_query(context)]
#                 self.collection.add(**params)
#             logger.info(f"Recorded new experience: {decision_id}")
#         except Exception as e:
#     pass
#             logger.error(f"Failed to record experience: {e}")
"""
def update_result(self, decision_id: str, pnl: float, result_summary: str):
        pass
        try:
# We fetch the existing entry, then update metadata
            results = self.collection.get(ids=[decision_id])
            if results and results["ids"]:
                metadata = results["metadatas"][0]
                metadata["pnl"] = float(pnl)
                metadata["result_summary"] = result_summary
                metadata["status"] = "CLOSED"
                    self.collection.update(ids=[decision_id], metadatas=[metadata])
                logger.info(f"Updated experience {decision_id} with PnL: {pnl:.2f}")
            else:
                logger.warning(f"Experience ID {decision_id} not found for update.")
        except Exception as e:
            logger.error(f"Failed to update experience: {e}")
    def retrieve_lessons(self, current_context: str, n_results: int = 3) -> List[Dict[str, Any]]:
        pass
#         """
#         Finds similar past contexts and extracts the lessons learned.
#                 try:
#     pass
#                     query_params = {"n_results": n_results}
#                 if self.embeddings:
#     pass
#                     query_params["query_embeddings"] = [self.embeddings.embed_query(current_context)]
#             else:
#     pass
#                 # Use Chroma's internal search with its default EF
#                 query_params["query_texts"] = [current_context]
#                 results = self.collection.query(**query_params)
#                 formatted = []
#             if results and results["documents"]:
#     pass
#                 for i in range(len(results["documents"][0])):
#     pass
#                     doc = results["documents"][0][i]
#                     meta = results["metadatas"][0][i]
#                     formatted.append(
#                         {
#                             "context": doc,
#                             "metadata": meta,
#                             "distance": results["distances"][0][i] if "distances" in results else 0,
#                         }
#                     )
#             return formatted
#         except Exception as e:
#     pass
#             logger.error(f"Failed to retrieve lessons: {e}")
#             return []
# """
