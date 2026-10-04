import pytest
from app.memory.long_term import LongTermMemory


def test_long_term_memory_crud_and_versioning(temp_chroma_dir, fast_embeddings):
    ltm = LongTermMemory(
        collection="test_crud",
        persist_dir=temp_chroma_dir,
        reset=True,
        embedding_function=fast_embeddings,
    )
    assert ltm.count() == 0

    # 1. Add
    mid = ltm.add("User's cloud GPU budget is $50 per month.", session_id="s1")
    assert mid is not None
    assert len(mid) == 8
    assert ltm.count() == 1

    item = ltm.get_by_id(mid)
    assert item is not None
    assert item["version"] == 1
    assert item["session_id"] == "s1"
    assert "$50" in item["text"]

    # 2. Update
    updated_id = ltm.update(mid, "User's cloud GPU budget is $80 per month.", session_id="s2")
    assert updated_id == mid
    assert ltm.count() == 1  # Count should NOT increase!

    item_v2 = ltm.get_by_id(mid)
    assert item_v2["version"] == 2
    assert "$80" in item_v2["text"]
    assert "$50" not in item_v2["text"]

    # 3. Persistence across re-open
    reopened = LongTermMemory(
        collection="test_crud",
        persist_dir=temp_chroma_dir,
        reset=False,
        embedding_function=fast_embeddings,
    )
    assert reopened.count() == 1
    reopened_item = reopened.get_by_id(mid)
    assert reopened_item["version"] == 2
    assert "$80" in reopened_item["text"]

    # 4. Search
    results = reopened.search("What is my budget?", k=2)
    assert len(results) >= 1
    assert "distance" in results[0]

    # 5. Delete
    deleted_id = reopened.delete(mid)
    assert deleted_id == mid
    assert reopened.count() == 0
    assert reopened.get_by_id(mid) is None
