"""
Flask web application for RAG Agent
"""
# Apply opentelemetry patch BEFORE importing anything that uses chromadb
import src.opentelemetry_patch  # noqa: F401

from flask import Flask, render_template, request, jsonify
from src.search import RAGSearch
from src.data_loader import get_collection_name_from_file, JSON_FILE_PATH
import os

app = Flask(__name__)

# Get collection name from JSON file name automatically
# Wrap in try-except to prevent app crash on startup
try:
    collection_name = get_collection_name_from_file(JSON_FILE_PATH)
    print(f"[INFO] Collection name determined: {collection_name}")
except Exception as e:
    print(f"[WARNING] Failed to get collection name: {e}")
    collection_name = "rag_documents"  # Default fallback

# Lazy initialization of RAG search to reduce memory usage at startup
# This will be initialized on first request
rag_search = None
rag_error = None

def get_rag_search():
    """Lazy initialization of RAG search with memory optimizations"""
    global rag_search, rag_error
    if rag_search is None and rag_error is None:
        try:
            import gc
            import torch
            
            print("[INFO] Initializing RAG Agent (lazy load)...")
            print(f"[INFO] Using JSON file: {JSON_FILE_PATH}")
            print(f"[INFO] Collection name: {collection_name}")
            
            # Clear any cached memory before loading model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            rag_search = RAGSearch(
                collection_name=collection_name,
                data_loader_module="src.data_loader"
            )
            
            # Clear memory after initialization
            gc.collect()
            
            print("[INFO] RAG Agent ready!")
        except Exception as e:
            print(f"[ERROR] Failed to initialize RAG Agent: {e}")
            import traceback
            traceback.print_exc()
            rag_error = str(e)
            raise
    elif rag_error:
        raise Exception(f"RAG Agent initialization failed: {rag_error}")
    return rag_search

@app.route('/')
def index():
    """Render the main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"[ERROR] Failed to render index: {e}")
        return f"Error loading page: {str(e)}", 500

@app.route('/api/query', methods=['POST'])
def query():
    """Handle query requests"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Please provide a question'
            }), 400
        
        print(f"[INFO] Received query: {question}")
        
        # Get RAG search instance (lazy initialization)
        rag = get_rag_search()
        
        # Get answer from RAG agent (top_k=1 for focused results)
        answer = rag.search_and_summarize(question, top_k=1)
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer
        })
        
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    """Health check endpoint - doesn't require RAG initialization"""
    return jsonify({
        'status': 'healthy',
        'app': 'running',
        'rag_initialized': rag_search is not None
    })

@app.route('/ready')
def ready():
    """Readiness check - verifies RAG agent is initialized"""
    try:
        rag = get_rag_search()
        return jsonify({'status': 'ready', 'rag_initialized': rag is not None})
    except Exception as e:
        return jsonify({'status': 'not ready', 'error': str(e)}), 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

