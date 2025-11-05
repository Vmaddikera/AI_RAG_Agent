from pathlib import Path
from typing import List, Any
from langchain_core.documents import Document
import json
import os
import re

# Configuration: Change this to your JSON file path
# Use relative path for deployment compatibility
JSON_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "courses_en.json")

def get_collection_name_from_file(file_path: str) -> str:
    """
    Extract collection name from JSON file path.
    Example: "D:/RAG_Agent/courses_en.json" -> "courses_en"
    """
    file_name = os.path.basename(file_path)
    collection_name = os.path.splitext(file_name)[0]  # Remove .json extension
    return collection_name

def load_all_documents(data_dir: str = None) -> List[Any]:
    """
    Generic JSON loader that works with any JSON structure.
    Automatically detects if JSON is array or object and processes accordingly.
    Collection name is derived from the JSON file name.
    """
    documents = []
    
    # Use the configured JSON file path
    json_file = os.path.abspath(JSON_FILE_PATH)
    
    if not os.path.exists(json_file):
        print(f"[ERROR] JSON file not found: {json_file}")
        return documents
    
    # Get collection name from file name
    collection_name = get_collection_name_from_file(json_file)
    print(f"[INFO] Loading data from: {json_file}")
    print(f"[INFO] Collection name will be: {collection_name}")
    
    try:
        # Use json.load() for better memory efficiency with large files
        with open(json_file, 'r', encoding='utf-8') as f:
            # For large files, parse directly without reading entire file
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                # If JSON is invalid, try to fix trailing commas
                f.seek(0)
                content = f.read()
                content = re.sub(r',(\s*[}\]])', r'\1', content)
                data = json.loads(content)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Array of objects (e.g., courses_en.json)
            print(f"[INFO] Detected array format with {len(data)} items")
            documents = _process_array_format(data, collection_name)
        elif isinstance(data, dict):
            # Object/dictionary format (e.g., IPL player stats)
            print(f"[INFO] Detected object/dictionary format with {len(data)} keys")
            documents = _process_dict_format(data, collection_name)
        else:
            print(f"[ERROR] Unsupported JSON format. Expected array or object.")
            return documents
        
        print(f"[INFO] Created {len(documents)} documents from JSON file")
        
    except Exception as e:
        print(f"[ERROR] Failed to load JSON file: {e}")
        import traceback
        traceback.print_exc()
        return documents

    return documents

def _process_array_format(data: List[dict], collection_name: str) -> List[Document]:
    """
    Process JSON array format (e.g., courses_en.json).
    Each item in the array becomes a document.
    """
    documents = []
    
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        
        # Build document text from all fields - prioritize important fields
        doc_text_parts = []
        
        # Important fields first (for better search relevance)
        priority_fields = ['name', 'content', 'what_you_learn', 'skills', 'category']
        
        # Add priority fields first
        for key in priority_fields:
            if key in item and item[key]:
                value = item[key]
                if isinstance(value, str) and value.strip():
                    doc_text_parts.append(f"{key}: {value}")
        
        # Add remaining fields
        for key, value in item.items():
            if key in priority_fields:  # Skip already added fields
                continue
            if value is None or value == "":
                continue
            
            if isinstance(value, list):
                # Handle arrays (e.g., instructors)
                if value:
                    doc_text_parts.append(f"{key}: {', '.join(str(v) for v in value)}")
            elif isinstance(value, dict):
                # Handle nested objects - simplify for search
                doc_text_parts.append(f"{key}: {str(value)}")
            else:
                doc_text_parts.append(f"{key}: {value}")
        
        doc_text = "\n".join(doc_text_parts)
        
        # Create metadata with essential fields only (to reduce size)
        metadata = {
            "source": collection_name,
            "index": idx,
        }
        
        # Add key fields to metadata
        if 'name' in item:
            metadata['name'] = str(item['name'])
        if 'category' in item:
            metadata['category'] = str(item['category'])
        if 'url' in item:
            metadata['url'] = str(item['url'])
        
        doc = Document(page_content=doc_text, metadata=metadata)
        documents.append(doc)
    
    return documents

def _process_dict_format(data: dict, collection_name: str) -> List[Document]:
    """
    Process JSON dictionary format (e.g., IPL player stats).
    This is a generic handler - you can customize based on your specific structure.
    """
    documents = []
    
    # Generic processing: each top-level key becomes a document
    for key, value in data.items():
        if isinstance(value, dict):
            # Nested structure - create document with all nested data
            doc_text_parts = [f"Key: {key}"]
            
            for sub_key, sub_value in value.items():
                if sub_value is None or sub_value == "":
                    continue
                
                if isinstance(sub_value, (dict, list)):
                    doc_text_parts.append(f"{sub_key}: {json.dumps(sub_value)}")
                else:
                    doc_text_parts.append(f"{sub_key}: {sub_value}")
            
            doc_text = "\n".join(doc_text_parts)
            
            metadata = {
                "source": collection_name,
                "key": key,
                **{k: str(v) if not isinstance(v, (dict, list)) else json.dumps(v) for k, v in value.items() if not isinstance(v, (dict, list))}
            }
            
            doc = Document(page_content=doc_text, metadata=metadata)
            documents.append(doc)
        else:
            # Simple key-value pair
            doc_text = f"Key: {key}\nValue: {value}"
            metadata = {
                "source": collection_name,
                "key": key,
                "value": str(value)
            }
            doc = Document(page_content=doc_text, metadata=metadata)
            documents.append(doc)
    
    return documents

# Example usage
if __name__ == "__main__":
    docs = load_all_documents()
    print(f"\nLoaded {len(docs)} documents.")
    if docs:
        print(f"\nExample document (first 500 chars):\n{docs[0].page_content[:500]}")
        print(f"\nExample metadata:\n{docs[0].metadata}")
        # Print collection name
        collection_name = get_collection_name_from_file(JSON_FILE_PATH)
        print(f"\nCollection name: {collection_name}")

