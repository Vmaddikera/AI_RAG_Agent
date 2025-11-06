import os
from typing import List, Any

# Try new packages first, fallback to deprecated ones
try:
    from langchain_chroma import Chroma
    CHROMA_IMPORTED = True
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
        CHROMA_IMPORTED = True
        print("[WARNING] Using deprecated Chroma import. Install 'langchain-chroma' to remove this warning.")
    except ImportError:
        CHROMA_IMPORTED = False
        print("[ERROR] ChromaDB not available. Install 'langchain-chroma' or 'langchain-community'")

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    EMBEDDINGS_IMPORTED = True
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        EMBEDDINGS_IMPORTED = True
        print("[WARNING] Using deprecated HuggingFaceEmbeddings import. Install 'langchain-huggingface' to remove this warning.")
    except ImportError:
        EMBEDDINGS_IMPORTED = False
        print("[ERROR] HuggingFace embeddings not available. Install 'langchain-huggingface' or 'langchain-community'")

class ChromaVectorStore:
    def __init__(self, persist_dir: str = "chroma_db", embedding_model: str = "all-MiniLM-L6-v2", chunk_size: int = 1000, chunk_overlap: int = 200, collection_name: str = "rag_documents"):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name
        
        # Initialize embeddings with memory optimizations
        # all-MiniLM-L6-v2 is already the smallest model (~80MB)
        # Using CPU device and ensuring efficient loading
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={
                'device': 'cpu'
            },
            encode_kwargs={
                'normalize_embeddings': True,  # Normalize for better performance
                'batch_size': 32  # Smaller batch size to reduce memory spikes
            }
        )
        print(f"[INFO] Loaded embedding model: {embedding_model} (CPU, optimized)")
        
        # Initialize ChromaDB
        self.vectorstore = None

    def build_from_documents(self, documents: List[Any], collection_name: str = "rag_documents"):
        print(f"[INFO] Building ChromaDB vector store from {len(documents)} documents...")
        
        # Create or get ChromaDB collection
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_dir,
            collection_name=collection_name
        )
        self.collection_name = collection_name
        print(f"[INFO] Vector store built and saved to {self.persist_dir} (collection: {collection_name})")

    def load(self):
        print(f"[INFO] Loading ChromaDB from {self.persist_dir} (collection: {self.collection_name})...")
        try:
            self.vectorstore = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
            # Check if collection has documents
            collection_count = self.vectorstore._collection.count()
            print(f"[INFO] Loaded ChromaDB from {self.persist_dir} (found {collection_count} documents)")
            if collection_count == 0:
                print("[WARNING] ChromaDB collection is empty! You may need to rebuild it.")
                return False
            return True
        except Exception as e:
            print(f"[WARNING] Failed to load ChromaDB: {e}")
            return False

    def query(self, query_text: str, top_k: int = 5):
        if self.vectorstore is None:
            loaded = self.load()
            if not loaded:
                return []
        
        print(f"[INFO] Querying vector store for: '{query_text}'")
        try:
            results = self.vectorstore.similarity_search_with_score(query_text, k=top_k)
            
            # Convert to expected format
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "score": float(score),
                    "metadata": doc.metadata,
                    "text": doc.page_content
                })
            return formatted_results
        except Exception as e:
            print(f"[ERROR] Query failed: {e}")
            return []


