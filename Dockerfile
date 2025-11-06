# Multi-stage build to reduce final image size
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in builder stage
WORKDIR /app
COPY requirements.txt .

# Install torch CPU-only first to avoid CUDA dependencies (saves ~3GB)
# This prevents sentence-transformers from pulling in CUDA-enabled torch
# Also upgrade opentelemetry early to fix Python 3.12 compatibility
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio && \
    pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user --upgrade 'opentelemetry-api>=1.28.0' 'opentelemetry-sdk>=1.28.0'

# Final stage - minimal runtime image
FROM python:3.12-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
WORKDIR /app
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Clean up Python cache and unnecessary files to reduce image size
# Note: Don't remove .dist-info as it breaks package metadata
RUN find /root/.local -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true && \
    find /root/.local -type f -name "*.pyc" -delete && \
    find /root/.local -type f -name "*.pyo" -delete && \
    find /root/.local -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /root/.local -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /root/.local -type d -name "docs" -exec rm -rf {} + 2>/dev/null || true && \
    find /root/.local -type d -name "doc" -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /root/.cache/pip 2>/dev/null || true

# Disable ChromaDB OpenTelemetry to avoid Python 3.12 compatibility issues
ENV CHROMA_OTEL_GRANULARITY=none

# Expose port
EXPOSE 8000

# Run gunicorn with 1 worker to reduce memory usage
# Each worker loads the embedding model (~200-400MB), so 1 worker is safer
CMD ["gunicorn", "app_prod:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "120"]

