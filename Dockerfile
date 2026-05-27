FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY scripts/ ./scripts/
COPY src/ ./src/
COPY pyproject.toml .

# Install package in development mode (if needed)
RUN pip install -e .

# Expose API port
EXPOSE 8000

# Health check - matches the docker-compose configuration
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=6 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)" || exit 1

# Run the FastAPI application with uvicorn
CMD ["uvicorn", "scripts.main_api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]