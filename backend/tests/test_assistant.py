import pytest
from app.memory.long_term import LongTermMemory
from app.agent.assistant import Assistant
from app.llm import FakeLLM
from app.tools.calculator import calculator


class ScriptedFakeAgent:
    """Fake ReAct agent runner that simulates reasoning and tool execution."""
    def __init__(self, reply: str = "Test response", invoke_calc: bool = False):
        self.reply = reply
        self.invoke_calc = invoke_calc

    def invoke(self, state, config=None):
        if self.invoke_calc:
            calculator.invoke({"expression": "10 + 20"})
        return {"messages": [{"role": "assistant", "content": self.reply}]}


def test_assistant_per_turn_flow(temp_chroma_dir, fast_embeddings):
    ltm = LongTermMemory(
        collection="test_assistant_flow",
        persist_dir=temp_chroma_dir,
        reset=True,
        embedding_function=fast_embeddings,
    )
    fake_updater_llm = FakeLLM(responses=[
        '{"ops": [{"op": "add", "text": "User is a senior software engineer."}]}'
    ])
    fake_agent = ScriptedFakeAgent(reply="Understood, I have noted that.", invoke_calc=True)

    bot = Assistant(
        ltm=ltm,
        session_id="sess_demo",
        agent_runner=fake_agent,
        updater_llm=fake_updater_llm,
    )

    res = bot.ask("I am a senior software engineer. Also calculate 10 + 20.")

    # 1. Reply
    assert "Understood" in res["reply"]

    # 2. Tool calls (per-turn isolated)
    assert len(res["tool_calls"]) == 1
    assert res["tool_calls"][0]["tool"] == "calculator"
    assert res["tool_calls"][0]["success"] is True

    # 3. Memory ops
    assert len(res["memory_ops"]) == 1
    assert res["memory_ops"][0]["op"] == "add"
    assert "software engineer" in res["memory_ops"][0]["text"]

    # 4. Long-term memory updated in Chroma
    assert ltm.count() == 1
    all_facts = ltm.all()
    assert len(all_facts) == 1
    assert all_facts[0]["version"] == 1
    assert "software engineer" in all_facts[0]["text"]

    # 5. Short-term buffer updated
    assert len(bot.stm) == 1
