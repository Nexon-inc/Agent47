from typing import List, Dict, Any, Optional, Union, Tuple
import json
import logging
from pathlib import Path
from ..config import settings

logger = logging.getLogger(__name__)

class ChromaDBManager:
    def __init__(self):
        # Delay importing chromadb and numpy until initialize() to avoid
        # expensive imports at module import time.
        self.client: Optional[Any] = None
        self.collections: Dict[str, Any] = {}
        self._initialized = False
        self.embedding_function = None
    
    async def initialize(self):
        if self._initialized:
            return
        
        try:
            # Import chromadb and heavy dependencies here, at runtime
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            from chromadb.utils import embedding_functions
            # numpy is only used by chromadb internals; import lazily if needed
            try:
                import numpy as np  # noqa: F401
            except Exception:
                # numpy may not be present in minimal envs; chromadb may still work depending on backend
                logger.debug("numpy not available at import; proceeding without it")

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.chroma.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Initialize embedding function with robust fallbacks.
            # Prefer a purely local embedding that doesn't require external API keys.
            try:
                import inspect

                def _safe_instantiate(klass, **kw):
                    """Instantiate klass by filtering kwargs to its __init__ signature.

                    Returns an instance or raises the underlying exception.
                    """
                    sig = inspect.signature(klass.__init__)
                    accepted = {p for p in sig.parameters.keys() if p != 'self'}
                    filtered = {k: v for k, v in kw.items() if k in accepted}
                    return klass(**filtered)

                # Priority order:
                # 1) If a local SentenceTransformer implementation exists, use it (no API keys).
                # 2) Try ONNX optimized MiniLM if available.
                # 3) If OpenAI configured, use that.
                # 4) As a last resort, attempt HuggingFaceEmbeddingFunction only if API key present.

                tried = []

                # 1) SentenceTransformerEmbeddingFunction (local)
                if hasattr(embedding_functions, 'SentenceTransformerEmbeddingFunction'):
                    try:
                        self.embedding_function = _safe_instantiate(
                            embedding_functions.SentenceTransformerEmbeddingFunction,
                            model_name="all-MiniLM-L6-v2",
                            device="cpu",
                            normalize_embeddings=False
                        )
                        logger.info("Using local SentenceTransformer embeddings (preferred)")
                    except Exception as e:
                        tried.append(('SentenceTransformer', str(e)))

                # 2) ONNX MiniLM variant
                if self.embedding_function is None and hasattr(embedding_functions, 'ONNXMiniLM_L6_V2'):
                    try:
                        self.embedding_function = _safe_instantiate(
                            embedding_functions.ONNXMiniLM_L6_V2
                        )
                        logger.info("Using ONNX MiniLM embeddings")
                    except Exception as e:
                        tried.append(('ONNXMiniLM', str(e)))

                # 3) OpenAI if configured
                if self.embedding_function is None and getattr(settings, 'openai', None) and getattr(settings.openai, 'openai_api_key', None):
                    try:
                        self.embedding_function = _safe_instantiate(
                            embedding_functions.OpenAIEmbeddingFunction,
                            api_key=settings.openai.openai_api_key,
                            model_name="text-embedding-ada-002"
                        )
                        logger.info("Using OpenAI embeddings (configured)")
                    except Exception as e:
                        tried.append(('OpenAI', str(e)))

                # 4) Finally, only attempt HuggingFaceEmbeddingFunction if an API key is available
                if self.embedding_function is None and hasattr(embedding_functions, 'HuggingFaceEmbeddingFunction'):
                    hf_api_key = None
                    if getattr(settings, 'grok', None) and getattr(settings.grok, 'api_key', None):
                        hf_api_key = getattr(settings.grok, 'api_key')
                    elif 'CHROMA_HUGGINGFACE_API_KEY' in (os.environ if 'os' in globals() else {}):
                        import os
                        hf_api_key = os.environ.get('CHROMA_HUGGINGFACE_API_KEY')

                    if hf_api_key:
                        try:
                            self.embedding_function = _safe_instantiate(
                                embedding_functions.HuggingFaceEmbeddingFunction,
                                api_key=hf_api_key,
                                model_name="sentence-transformers/all-MiniLM-L6-v2"
                            )
                            logger.info("Using HuggingFace embedding function with configured API key")
                        except Exception as e:
                            tried.append(('HuggingFace', str(e)))

                # If nothing worked, raise a helpful error
                if self.embedding_function is None:
                    logger.warning(f"Embedding initialization attempts: {tried}")
                    raise Exception("No working embedding function available")

            except Exception as e:
                logger.error(f"Failed to initialize embedding function: {e}")
                raise

            # Create default collections
            await self._create_default_collections()

            self._initialized = True
            logger.info("ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def _create_default_collections(self):
        """Create default collections for the system"""
        default_collections = [
            "research_data",
            "user_preferences", 
            "agent_knowledge",
            "content_embeddings",
            "search_results",
            "task_contexts"
        ]
        
        for collection_name in default_collections:
            try:
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"description": f"Default collection for {collection_name}"}
                )
                self.collections[collection_name] = collection
                logger.info(f"Collection {collection_name} initialized")
            except Exception as e:
                logger.error(f"Failed to create collection {collection_name}: {e}")
    
    async def close(self):
        """Close ChromaDB connections"""
        if self.client:
            try:
                # Some Chroma client implementations may not expose persist().
                # Guard the call to avoid AttributeError during shutdown.
                if hasattr(self.client, 'persist') and callable(getattr(self.client, 'persist')):
                    self.client.persist()
            except Exception as e:
                logger.warning(f"Failed to persist chroma client during close: {e}")
            finally:
                self._initialized = False
                logger.info("ChromaDB connections closed")
    
    async def health_check(self) -> bool:
        """Check ChromaDB health"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Try to access a collection
            test_collection = self.client.get_collection("research_data")
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False
    
    async def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """Get or create a collection"""
        if not self._initialized:
            await self.initialize()
        
        if name not in self.collections:
            try:
                collection = self.client.get_or_create_collection(
                    name=name,
                    embedding_function=self.embedding_function,
                    metadata=metadata or {}
                )
                self.collections[name] = collection
                logger.info(f"Collection {name} created/retrieved")
            except Exception as e:
                logger.error(f"Failed to get/create collection {name}: {e}")
                raise
        
        return self.collections[name]
    
    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add documents to a collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            
            # Generate IDs if not provided
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Add documents to collection
            collection.add(
                documents=documents,
                metadatas=metadatas or [{} for _ in documents],
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection {collection_name}")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add documents to collection {collection_name}: {e}")
            raise
    
    async def query_documents(
        self,
        collection_name: str,
        query_texts: List[str],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query documents from a collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            
            logger.info(f"Queried collection {collection_name} with {len(query_texts)} queries")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query collection {collection_name}: {e}")
            raise
    
    async def update_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Update documents in a collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            
            collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Updated {len(ids)} documents in collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update documents in collection {collection_name}: {e}")
            return False
    
    async def delete_documents(self, collection_name: str, ids: List[str]) -> bool:
        """Delete documents from a collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            
            collection.delete(ids=ids)
            
            logger.info(f"Deleted {len(ids)} documents from collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from collection {collection_name}: {e}")
            return False
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            
            info = {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return {}
    
    async def list_collections(self) -> List[str]:
        """List all collections"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            self.client.delete_collection(collection_name)
            
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            logger.info(f"Collection {collection_name} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    async def reset_collection(self, collection_name: str) -> bool:
        """Reset a collection (delete all documents)"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            
            # Get all document IDs
            all_docs = collection.get()
            if all_docs["ids"]:
                collection.delete(ids=all_docs["ids"])
            
            logger.info(f"Collection {collection_name} reset")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection {collection_name}: {e}")
            return False
    
    async def similarity_search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 10,
        threshold: float = 0.7,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform similarity search with threshold filtering"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results * 2,  # Get more results to filter by threshold
                where=where
            )
            
            # Filter results by similarity threshold
            filtered_results = []
            if results["distances"] and results["distances"][0]:
                for i, distance in enumerate(results["distances"][0]):
                    if distance <= threshold:
                        filtered_results.append({
                            "id": results["ids"][0][i],
                            "document": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": distance
                        })
                
                # Sort by distance and limit results
                filtered_results.sort(key=lambda x: x["distance"])
                filtered_results = filtered_results[:n_results]
            
            logger.info(f"Similarity search completed for collection {collection_name}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search in collection {collection_name}: {e}")
            return []
    
    async def batch_operations(
        self,
        collection_name: str,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform batch operations on a collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            
            results = {
                "added": 0,
                "updated": 0,
                "deleted": 0,
                "errors": []
            }
            
            for operation in operations:
                try:
                    op_type = operation.get("type")
                    
                    if op_type == "add":
                        collection.add(
                            documents=operation["documents"],
                            metadatas=operation.get("metadatas"),
                            ids=operation.get("ids")
                        )
                        results["added"] += len(operation["documents"])
                    
                    elif op_type == "update":
                        collection.update(
                            ids=operation["ids"],
                            documents=operation.get("documents"),
                            metadatas=operation.get("metadatas")
                        )
                        results["updated"] += len(operation["ids"])
                    
                    elif op_type == "delete":
                        collection.delete(ids=operation["ids"])
                        results["deleted"] += len(operation["ids"])
                    
                except Exception as e:
                    results["errors"].append({
                        "operation": operation,
                        "error": str(e)
                    })
            
            logger.info(f"Batch operations completed for collection {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform batch operations on collection {collection_name}: {e}")
            raise

# Global ChromaDB manager instance
chroma_manager = ChromaDBManager()

async def get_chroma() -> ChromaDBManager:
    return chroma_manager

async def init_chroma():
    await chroma_manager.initialize()

async def close_chroma():
    await chroma_manager.close()


# Backwards-compatible alias: some modules import ChromaManager
# while the concrete class is named ChromaDBManager in this module.
ChromaManager = ChromaDBManager
