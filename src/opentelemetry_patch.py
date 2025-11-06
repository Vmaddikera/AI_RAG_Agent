"""
Patch for opentelemetry Python 3.12 compatibility issue
This must be imported before chromadb to fix the StopIteration error
"""
import os

# Disable ChromaDB OpenTelemetry to prevent it from initializing
# This is the primary fix - if opentelemetry isn't initialized, the error won't occur
os.environ.setdefault('CHROMA_OTEL_GRANULARITY', 'none')
os.environ.setdefault('CHROMA_OTEL_COLLECTION_ENDPOINT', '')
os.environ.setdefault('CHROMA_OTEL_SERVICE_NAME', '')

