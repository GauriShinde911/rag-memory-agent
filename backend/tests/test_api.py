import pytest
from starlette.testclient import TestClient

from app.main import app
from app.memory.long_term import LongTermMemory
from app.agent.assistant import Assistant
from app.api.routes import _sessions
import app.api.routes as routes_module
from app.llm import FakeLLM


class MockAgent:
    def invoke(self, state, config=None):
        return {"messages": [{"role": "assistant", "content": "I am a helpful assistant."}]}


@pytest.fixture
def client(temp_chroma_dir, fast_embeddings):
    # Set up isolated test memory for the API client
    test_ltm = LongTermMemory(
        collection="test_api_memory",
        persist_dir=temp_chroma_dir,
        reset=True,
        embedding_function=fast_embeddings,
    )
    # Monkeypatch live LTM getter
    routes_module._live_ltm = test_ltm
    routes_module._sessions.clear()

    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "provider" in data
    assert "model" in data


def test_session_lifecycle(client):
    # Create new session
    res = client.post("/api/sessions", json={"session_id": "test_sess_1"})
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == "test_sess_1"
    assert "test_sess_1" in routes_module._sessions

    # Reset existing session
    res2 = client.post("/api/sessions", json={"session_id": "test_sess_1"})
    assert res2.status_code == 200
    assert "reset" in res2.json()["message"]


def test_memory_crud_api(client):
    # 1. Add via direct LTM
    ltm = routes_module.get_live_ltm()
    mid = ltm.add("User's favourite IDE is Antigravity.", session_id="test")

    # 2. List memories
    res = client.get("/api/memory")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["memories"][0]["id"] == mid
    assert data["memories"][0]["version"] == 1

    # 3. Update memory
    patch_res = client.patch(f"/api/memory/{mid}", json={"text": "User's favourite IDE is Antigravity 2.0."})
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["memory"]["version"] == 2
    assert "2.0" in updated_data["memory"]["text"]

    # 4. Search memory filter
    search_res = client.get("/api/memory?search=Antigravity")
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 1

    search_miss = client.get("/api/memory?search=nonexistent")
    assert search_miss.status_code == 200
    assert search_miss.json()["total"] == 0

    # 5. Delete memory
    del_res = client.delete(f"/api/memory/{mid}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    list_after = client.get("/api/memory")
    assert list_after.json()["total"] == 0


def test_chat_turn_endpoint(client):
    # Inject fake assistant for session
    sess_id = "chat_test_sess"
    fake_updater = FakeLLM(responses=['{"ops": [{"op": "add", "text": "User is building a library chatbot."}]}'])
    bot = Assistant(
        ltm=routes_module.get_live_ltm(),
        session_id=sess_id,
        agent_runner=MockAgent(),
        updater_llm=fake_updater,
    )
    routes_module._sessions[sess_id] = bot

    res = client.post("/api/chat", json={"session_id": sess_id, "message": "I am building a library chatbot."})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "retrieved" in data
    assert "tool_calls" in data
    assert "memory_ops" in data
    assert len(data["memory_ops"]) == 1
    assert data["memory_ops"][0]["op"] == "add"


def test_live_metrics_endpoint(client):
    res = client.get("/api/metrics/live")
    assert res.status_code == 200
    data = res.json()
    assert "total_calls" in data
    assert "success_rate" in data
    assert "by_tool" in data
