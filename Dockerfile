FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Model layer — deliberately BEFORE pyproject.toml is copied. semantic-release
# bumps the version in pyproject on every release, and if that file were copied
# first, each bump would invalidate this layer and re-download ~2.3GB of model
# weights on every rebuild. Pinning the two libraries the downloads need keeps
# this layer stable across releases.
RUN pip install --no-cache-dir "sentence-transformers>=3.0.0" "spacy>=3.7.0"
RUN python -m spacy download en_core_web_sm
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .
