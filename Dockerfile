FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
RUN python -m spacy download en_core_web_sm
# Pre-download the embedding model so workers don't pay a cold-start fetch.
# bge-m3 is ~2.3GB, so this dominates image build time and size.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

COPY . .
