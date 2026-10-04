import pytest
from app.memory.long_term import LongTermMemory
from app.memory.updater import MemoryUpdater
from app.llm import FakeLLM


def test_updater_add_operation(temp_chroma_dir, fast_embeddings):
    ltm = LongTermMemory(
        collection="test_updater_add",
        persist_dir=temp_chroma_dir,
        reset=True,
        embedding_function=fast_embeddings,
    )
    fake_llm = FakeLLM(responses=[
        '{"ops": [{"op": "add", "text": "User is studying transformer architectures."}]}'
    ])
    updater = MemoryUpdater(llm=fake_llm)

    res = updater.adapt(
        ltm=ltm,
        user_msg="I am doing a study on transformers.",
        reply="That sounds great!",
        retrieved_mems=[],
        session_id="s1",
    )
    assert len(res.applied) == 1
    assert res.applied[0]["op"] == "add"
    assert "transformer" in res.applied[0]["text"]
    assert len(res.skipped) == 0
    assert ltm.count() == 1


def test_updater_update_with_valid_and_invalid_ids(temp_chroma_dir, fast_embeddings):
    ltm = LongTermMemory(
        collection="test_updater_upd",
        persist_dir=temp_chroma_dir,
        reset=True,
        embedding_function=fast_embeddings,
    )
    real_id = ltm.add("User GPU budget is $50/mo.", session_id="s1")

    # LLM attempts to update valid ID and a bogus/unretrieved ID "bad999"
    fake_llm = FakeLLM(responses=[
        f'{{"ops": ['
        f'{{"op": "update", "id": "{real_id}", "text": "User GPU budget is $80/mo."}},'
        f'{{"op": "update", "id": "bad999", "text": "Some unretrieved fact"}}'
        f']}}'
    ])
    updater = MemoryUpdater(llm=fake_llm)

    # Only real_id was retrieved in this turn!
    retrieved = [{"id": real_id, "text": "User GPU budget is $50/mo."}]

    res = updater.adapt(
        ltm=ltm,
        user_msg="My GPU budget was increased to $80.",
        reply="I updated your budget.",
        retrieved_mems=retrieved,
        session_id="s2",
    )

    assert len(res.applied) == 1
    assert res.applied[0]["op"] == "update"
    assert res.applied[0]["id"] == real_id

    # The bad999 op must be safely skipped!
    assert len(res.skipped) == 1
    assert res.skipped[0]["id"] == "bad999"
    assert "not in retrieved memories" in res.skipped[0]["reason"]

    # Verify LTM state: version is bumped to 2
    item = ltm.get_by_id(real_id)
    assert item["version"] == 2
    assert "$80" in item["text"]


def test_updater_resilient_to_invalid_json(temp_chroma_dir, fast_embeddings):
    ltm = LongTermMemory(
        collection="test_updater_broken",
        persist_dir=temp_chroma_dir,
        reset=True,
        embedding_function=fast_embeddings,
    )
    fake_llm = FakeLLM(responses=["Sorry, I cannot produce JSON right now."])
    updater = MemoryUpdater(llm=fake_llm)

    res = updater.adapt(
        ltm=ltm,
        user_msg="Hello",
        reply="Hi there",
        retrieved_mems=[],
    )
    # Never raises, records in skipped
    assert len(res.applied) == 0
    assert len(res.skipped) == 1
    assert "No JSON block found" in res.skipped[0]["reason"]
