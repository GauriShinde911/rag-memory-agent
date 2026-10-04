import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Global singleton embedding function to avoid reloading weights repeatedly
_GLOBAL_EMBEDDINGS = None
_EMBEDDINGS_STATUS = "loading"


def get_embedding_function(model_name: Optional[str] = None):
    """Retrieve or initialize the HuggingFace embeddings singleton."""
    global _GLOBAL_EMBEDDINGS, _EMBEDDINGS_STATUS
    if _GLOBAL_EMBEDDINGS is None:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            name = model_name or settings.embedding_model
            _GLOBAL_EMBEDDINGS = HuggingFaceEmbeddings(model_name=name)
            _EMBEDDINGS_STATUS = "ready"
            logger.info(f"Loaded embeddings model: {name}")
        except Exception as e:
            logger.error(f"Failed to load embeddings model: {e}")
            _EMBEDDINGS_STATUS = "error"
            raise e
    return _GLOBAL_EMBEDDINGS


def get_embeddings_status() -> str:
    """Return 'loading', 'ready', or 'error' for health checks."""
    return _EMBEDDINGS_STATUS


def warmup_embeddings() -> None:
    """Trigger embedding model load in background/lifespan."""
    try:
        get_embedding_function()
    except Exception as e:
        logger.error(f"Error during embeddings warmup: {e}")


class LongTermMemory:
    """Persistent Chroma vector memory wrapper with cosine similarity and versioning."""

    def __init__(
        self,
        collection: Optional[str] = None,
        persist_dir: Optional[str] = None,
        reset: bool = False,
        embedding_function=None,
    ):
        self.collection_name = collection or settings.collection_name
        self.persist_dir = persist_dir or settings.persist_dir
        self.emb = embedding_function or get_embedding_function()
        self.audit: List[Dict[str, Any]] = []

        os.makedirs(self.persist_dir, exist_ok=True)
        self.vs = self._open()

        if reset:
            try:
                self.vs.delete_collection()
            except Exception as e:
                logger.debug(f"Delete collection notice (safe to ignore if fresh): {e}")
            self.vs = self._open()

    def _open(self):
        from langchain_chroma import Chroma
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self.emb,
            persist_directory=self.persist_dir,
            collection_metadata={"hnsw:space": "cosine"},
        )

    def add(self, text: str, session_id: str = "na") -> str:
        """Add a new memory with version 1 and return its 8-char hex id."""
        mid = uuid.uuid4().hex[:8]
        now = datetime.now().isoformat()
        metadata = {
            "id": mid,
            "session_id": str(session_id),
            "created_at": now,
            "version": 1,
        }
        self.vs.add_texts([text], metadatas=[metadata], ids=[mid])
        self.audit.append({"op": "add", "id": mid, "text": text, "session": session_id})
        logger.info(f"LTM [{self.collection_name}] ADD [{mid}]: {text}")
        return mid

    def update(self, mid: str, new_text: str, session_id: str = "na") -> Optional[str]:
        """Update an existing memory by id, incrementing its version."""
        old = self.vs.get(ids=[mid])
        if not old or not old.get("ids"):
            logger.warning(f"LTM [{self.collection_name}] UPDATE failed: id '{mid}' not found")
            return None

        old_meta = old["metadatas"][0] if old.get("metadatas") else {}
        old_text = old["documents"][0] if old.get("documents") else ""
        new_version = int(old_meta.get("version", 1)) + 1
        now = datetime.now().isoformat()

        updated_metadata = {
            "id": mid,
            "session_id": str(session_id),
            "created_at": old_meta.get("created_at", now),
            "updated_at": now,
            "version": new_version,
        }

        # Replace document with identical ID and bumped version
        self.vs.delete(ids=[mid])
        self.vs.add_texts([new_text], metadatas=[updated_metadata], ids=[mid])
        self.audit.append({
            "op": "update",
            "id": mid,
            "old": old_text,
            "text": new_text,
            "session": session_id,
            "version": new_version,
        })
        logger.info(f"LTM [{self.collection_name}] UPDATE [{mid}] v{new_version}: {new_text}")
        return mid

    def delete(self, mid: str) -> Optional[str]:
        """Delete a memory by id."""
        old = self.vs.get(ids=[mid])
        if not old or not old.get("ids"):
            logger.warning(f"LTM [{self.collection_name}] DELETE failed: id '{mid}' not found")
            return None

        old_text = old["documents"][0] if old.get("documents") else ""
        self.vs.delete(ids=[mid])
        self.audit.append({"op": "delete", "id": mid, "old": old_text})
        logger.info(f"LTM [{self.collection_name}] DELETE [{mid}]: {old_text}")
        return mid

    def search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Search memory with cosine distance (0.0 = identical)."""
        g = self.vs.get()
        n = len(g["ids"]) if g and g.get("ids") else 0
        if n == 0:
            return []

        hits = self.vs.similarity_search_with_score(query, k=min(k, n))
        results = []
        for d, score in hits:
            # Extract id
            item_id = getattr(d, "id", None) or (d.metadata.get("id") if hasattr(d, "metadata") else None)
            meta = getattr(d, "metadata", {}) or {}
            results.append({
                "id": str(item_id) if item_id else None,
                "text": d.page_content,
                "distance": round(float(score), 4),
                "metadata": meta,
            })
        return results

    def all(self) -> List[Dict[str, Any]]:
        """Return all memories formatted as dictionaries."""
        g = self.vs.get()
        if not g or not g.get("ids"):
            return []

        out = []
        ids = g.get("ids", [])
        docs = g.get("documents", [])
        metas = g.get("metadatas", []) or [{}] * len(ids)

        for mid, doc, meta in zip(ids, docs, metas):
            m = meta or {}
            out.append({
                "id": mid,
                "text": doc,
                "version": m.get("version", 1),
                "session_id": m.get("session_id", "na"),
                "created_at": m.get("created_at", ""),
                "updated_at": m.get("updated_at"),
            })
        return out

    def get_by_id(self, mid: str) -> Optional[Dict[str, Any]]:
        """Retrieve single memory by id."""
        old = self.vs.get(ids=[mid])
        if not old or not old.get("ids"):
            return None
        meta = old["metadatas"][0] if old.get("metadatas") else {}
        return {
            "id": mid,
            "text": old["documents"][0],
            "version": meta.get("version", 1),
            "session_id": meta.get("session_id", "na"),
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at"),
        }

    def count(self) -> int:
        g = self.vs.get()
        return len(g.get("ids", [])) if g else 0
