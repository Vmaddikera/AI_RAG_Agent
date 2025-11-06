import os
from dotenv import load_dotenv
from src.vectorstore import ChromaVectorStore
from langchain_groq import ChatGroq

load_dotenv()

class RAGSearch:
    def __init__(self, persist_dir: str = "chroma_db", embedding_model: str = "all-MiniLM-L6-v2", llm_model: str = "llama-3.1-8b-instant", collection_name: str = "rag_documents", data_loader_module: str = "src.data_loader"):
        self.collection_name = collection_name



        self.vectorstore = ChromaVectorStore(persist_dir, embedding_model, collection_name=collection_name)
        # Load or build vectorstore
        chroma_path = os.path.join(persist_dir, "chroma.sqlite3")
        if not os.path.exists(chroma_path):
            print("[INFO] ChromaDB not found, building from documents...")
            self._load_and_build(data_loader_module)
        else:
            loaded = self.vectorstore.load()
            if not loaded:
                # Collection is empty, rebuild it
                print("[INFO] ChromaDB collection is empty, rebuilding...")
                self._load_and_build(data_loader_module)
        
        # Initialize LLM
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=llm_model)
        print(f"[INFO] Groq LLM initialized: {llm_model}")
    
    def _load_and_build(self, data_loader_module: str):
        """Helper to load data and build vectorstore"""
        import importlib
        module = importlib.import_module(data_loader_module)
        docs = module.load_all_documents()
        self.vectorstore.build_from_documents(docs, collection_name=self.collection_name)

    def search_and_summarize(self, query: str, top_k: int = 1) -> str:
        # Generic search - no player-specific filtering
        # Just perform vector similarity search
        results = self.vectorstore.query(query, top_k=top_k)
        
        texts = [r.get("text", "") for r in results]
        context = "\n\n".join(texts)
        
        if not context:
            return "No relevant documents found. Please try rephrasing your question."
        
        # Generic prompt for any domain
        prompt = f"""You are a helpful assistant. Answer the following question using ONLY the provided context data.

Question: {query}

Context Data:
{context}

Instructions:
1. Extract ALL relevant information from the context to answer the question
2. Provide a clear, detailed answer in natural, conversational paragraphs (like ChatGPT)
3. Write in flowing paragraphs, not bullet points or structured blocks
4. Use natural transitions between sentences and ideas
5. Be specific and accurate - only use information from the provided context
6. If comparing items, provide information for ALL items mentioned in a natural narrative style
7. If the context doesn't contain enough information to answer the question, say so

Answer in natural paragraphs:"""
        
        response = self.llm.invoke([prompt])
        return response.content

# Example usage