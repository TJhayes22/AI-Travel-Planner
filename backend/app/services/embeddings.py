"""Embedding generation for search queries, with simple in-process caching.

Caching note: this cache is a plain in-memory dict, scoped to this single
running process. It resets on restart and isn't shared across multiple server
instances. That's a deliberate, minimal starting point -- it eliminates the
most common case (the same search repeated in one dev/user session) without
standing up Redis before there's evidence it's needed. Revisit if this ever
runs as multiple processes/instances in production.
"""

from __future__ import annotations

from app.config import get_settings

EMBEDDING_MODEL = "text-embedding-3-small"

# module-level cache: normalized query text -> embedding vector
_query_embedding_cache: dict[str, list[float]] = {}


def _normalize(text: str) -> str:
    return text.strip().lower()


def get_query_embedding(text: str) -> list[float]:
    """Returns an embedding for the given search query text, using a cached
    value if this exact (normalized) text was embedded before in this process."""
    key = _normalize(text)

    if key in _query_embedding_cache:
        return _query_embedding_cache[key]

    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.embeddings.create(model=EMBEDDING_MODEL, input=[text])
    embedding = response.data[0].embedding

    _query_embedding_cache[key] = embedding
    return embedding