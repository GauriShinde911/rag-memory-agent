import pytest
from app.memory.short_term import ShortTermMemory


def test_short_term_memory_sliding_window():
    stm = ShortTermMemory(max_turns=3)
    assert len(stm) == 0

    stm.add("Turn 1 user", "Turn 1 ai")
    stm.add("Turn 2 user", "Turn 2 ai")
    assert len(stm) == 2

    stm.add("Turn 3 user", "Turn 3 ai")
    assert len(stm) == 3

    # Add 4th turn; turn 1 must be evicted
    stm.add("Turn 4 user", "Turn 4 ai")
    assert len(stm) == 3

    history = stm.get_history()
    assert history[0]["user"] == "Turn 2 user"
    assert history[-1]["user"] == "Turn 4 user"

    # LangChain messages formatting check
    messages = stm.messages()
    assert len(messages) == 6  # 3 pairs * 2


def test_short_term_memory_clear():
    stm = ShortTermMemory(max_turns=5)
    stm.add("Hi", "Hello")
    assert len(stm) == 1
    stm.clear()
    assert len(stm) == 0
    assert len(stm.messages()) == 0
