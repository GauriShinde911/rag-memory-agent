import logging
from typing import Any, Dict, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.memory.updater import MemoryUpdater, format_memories_for_prompt
from app.tools import TOOLS, current_turn_tools
from app.agent.prompts import SYSTEM_PROMPT
from app.llm import get_llm, text_of

logger = logging.getLogger(__name__)


def create_default_agent_runner(llm=None):
    """Build LangGraph create_react_agent with the default tools, or mock runner for FakeLLM."""
    from app.llm import FakeLLM
    active_llm = llm or get_llm(temperature=0.0)
    if isinstance(active_llm, FakeLLM):
        class SimpleFakeRunner:
            def __init__(self, fake_model):
                self.fake_model = fake_model
            def invoke(self, state, config=None):
                res = self.fake_model.invoke(state)
                return {"messages": [{"role": "assistant", "content": res.content}]}
        return SimpleFakeRunner(active_llm)

    from langgraph.prebuilt import create_react_agent
    return create_react_agent(active_llm, TOOLS)


class Assistant:
    """Coordinates retrieval, ReAct reasoning, short-term buffer, and memory adaptation."""

    def __init__(
        self,
        ltm: LongTermMemory,
        session_id: str,
        k: int = 4,
        window: int = 8,
        agent_runner=None,
        updater_llm=None,
    ):
        self.ltm = ltm
        self.session_id = session_id
        self.k = k
        self.stm = ShortTermMemory(window)
        self.agent_runner = agent_runner or create_default_agent_runner(updater_llm)
        self.updater = MemoryUpdater(llm=updater_llm)

    def ask(self, user_msg: str) -> Dict[str, Any]:
        """Perform a single interactive turn with explainable trace."""
        # 1. Retrieve top-k memories
        retrieved = self.ltm.search(user_msg, k=self.k)

        # 2. Setup request-scoped tool collector for this turn
        turn_tool_calls: List[Dict[str, Any]] = []
        token = current_turn_tools.set(turn_tool_calls)

        # 3. Assemble prompt: System + retrieved memories + STM history + new message
        formatted_mems = format_memories_for_prompt(retrieved)
        system_content = SYSTEM_PROMPT.format(memories=formatted_mems)
        msgs = (
            [SystemMessage(content=system_content)]
            + self.stm.messages()
            + [HumanMessage(content=user_msg)]
        )

        # 4. Reason and act
        try:
            out = self.agent_runner.invoke(
                {"messages": msgs},
                {"recursion_limit": 12},
            )
            if isinstance(out, dict) and "messages" in out and out["messages"]:
                last_msg = out["messages"][-1]
                if hasattr(last_msg, "content"):
                    reply = text_of(last_msg.content)
                elif isinstance(last_msg, dict):
                    reply = text_of(last_msg.get("content", ""))
                else:
                    reply = text_of(last_msg)
            elif hasattr(out, "content"):
                reply = text_of(out.content)
            else:
                reply = str(out)
        except Exception as e:
            logger.error(f"Agent reasoning error: {type(e).__name__}: {e}")
            reply = f"(agent error: {type(e).__name__}: {e})"
        finally:
            # Always reset contextvar
            current_turn_tools.reset(token)

        # 5. Append exchange to short-term memory buffer
        self.stm.add(user_msg, reply)

        # 6. Adapt long-term memory via feedback loop
        adapt_res = self.updater.adapt(
            ltm=self.ltm,
            user_msg=user_msg,
            reply=reply,
            retrieved_mems=retrieved,
            session_id=self.session_id,
        )

        return {
            "reply": reply,
            "retrieved": retrieved,
            "tool_calls": turn_tool_calls,
            "memory_ops": adapt_res.applied,
            "skipped_ops": adapt_res.skipped,
        }
