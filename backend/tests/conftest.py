import os
import shutil
import tempfile
import hashlib
import numpy as np
import pytest
from typing import List
from app.llm import FakeLLM


class FastTestEmbeddings:
    """Fast, deterministic, offline mock embeddings for instantaneous tests."""
    def __init__(self, dim: int = 384):
        self.dim = dim

    def _embed(self, text: str) -> List[float]:
        # Hash text to deterministic vector
        h = hashlib.sha256(text.lower().encode("utf-8")).digest()
        # Create reproducible vector
        np.random.seed(int.from_bytes(h[:4], "little"))
        vec = np.random.randn(self.dim)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


@pytest.fixture
def fast_embeddings():
    return FastTestEmbeddings()


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary directory for Chroma DB and clean up afterward."""
    temp_dir = tempfile.mkdtemp(prefix="test_chroma_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def fake_llm():
    """Return a fresh instance of FakeLLM."""
    return FakeLLM()
