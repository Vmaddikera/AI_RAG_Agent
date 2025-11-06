"""
Flask web application for RAG Agent
"""
import os
import sys

# Apply opentelemetry patch BEFORE importing anything that uses chromadb
try:
    import src.opentelemetry_patch  # noqa: F401
except Exception as e:
    print(f"[WARNING] Failed to load opentelemetry patch: {e}")

from flask import Flask, render_template, request, jsonify

# Try to import RAG components, but don't fail if they're not available
try:
    from src.search import RAGSearch
    from src.data_loader import get_collection_name_from_file, JSON_FILE_PATH
    RAG_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Failed to import RAG components: {e}")
    RAG_AVAILABLE = False
    JSON_FILE_PATH = None

app = Flask(__name__)

# Get collection name from JSON file name automatically
# Wrap in try-except to prevent app crash on startup
if RAG_AVAILABLE and JSON_FILE_PATH:
    try:
        collection_name = get_collection_name_from_file(JSON_FILE_PATH)
        print(f"[INFO] Collection name determined: {collection_name}")
    except Exception as e:
        print(f"[WARNING] Failed to get collection name: {e}")
        collection_name = "rag_documents"  # Default fallback
else:
    collection_name = "rag_documents"  # Default fallback
    print("[WARNING] RAG not available, using default collection name")

# Lazy initialization of RAG search to reduce memory usage at startup
# This will be initialized on first request
rag_search = None
rag_error = None

def get_rag_search():
    """Lazy initialization of RAG search with memory optimizations"""
    global rag_search, rag_error
    
    if not RAG_AVAILABLE:
        raise Exception("RAG components are not available. Check imports and dependencies.")
    
    if rag_search is None and rag_error is None:
        try:
            import gc
            
            print("[INFO] Initializing RAG Agent (lazy load)...")
            if JSON_FILE_PATH:
                print(f"[INFO] Using JSON file: {JSON_FILE_PATH}")
            print(f"[INFO] Collection name: {collection_name}")
            
            # Clear any cached memory before loading model
            gc.collect()
            
            # Try to import torch for CUDA cache clearing (optional)
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass  # Torch not available, skip
            
            rag_search = RAGSearch(
                collection_name=collection_name,
                data_loader_module="src.data_loader"
            )
            
            # Clear memory after initialization
            gc.collect()
            
            print("[INFO] RAG Agent ready!")
        except MemoryError as e:
            error_msg = f"Out of memory during RAG initialization: {e}"
            print(f"[ERROR] {error_msg}")
            rag_error = error_msg
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to initialize RAG Agent: {e}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            rag_error = error_msg
            raise Exception(error_msg)
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
        'rag_available': RAG_AVAILABLE,
        'rag_initialized': rag_search is not None,
        'rag_error': rag_error if 'rag_error' in globals() else None
    })

@app.route('/ready')
def ready():
    """Readiness check - verifies RAG agent is initialized"""
    if not RAG_AVAILABLE:
        return jsonify({
            'status': 'not ready',
            'error': 'RAG components not available',
            'rag_available': False
        }), 503
    
    try:
        rag = get_rag_search()
        return jsonify({
            'status': 'ready',
            'rag_initialized': rag is not None,
            'rag_available': True
        })
    except Exception as e:
        return jsonify({
            'status': 'not ready',
            'error': str(e),
            'rag_available': True
        }), 503

@app.route('/debug')
def debug():
    """Debug endpoint to check system status"""
    import sys
    import platform
    
    info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'rag_available': RAG_AVAILABLE,
        'rag_initialized': rag_search is not None,
        'rag_error': rag_error if 'rag_error' in globals() else None,
        'json_file_path': str(JSON_FILE_PATH) if JSON_FILE_PATH else None,
        'collection_name': collection_name if 'collection_name' in globals() else None
    }
    
    # Try to get memory info if available
    try:
        import psutil
        info['memory'] = {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent
        }
    except ImportError:
        info['memory'] = 'psutil not available'
    
    return jsonify(info)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

