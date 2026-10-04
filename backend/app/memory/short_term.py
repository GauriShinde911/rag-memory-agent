from typing import List, Tuple, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class ShortTermMemory:
    """Conversation buffer that keeps the last `max_turns` user/assistant exchanges of ONE session."""

    def __init__(self, max_turns: int = 8):
        self.max_turns = max_turns
        self._turns: List[Tuple[HumanMessage, AIMessage]] = []

    def add(self, user_text: str, ai_text: str) -> None:
        """Add a user/assistant exchange and maintain sliding window."""
        self._turns.append((HumanMessage(content=user_text), AIMessage(content=ai_text)))
        if len(self._turns) > self.max_turns:
            self._turns = self._turns[-self.max_turns:]

    def messages(self) -> List[BaseMessage]:
        """Return flat list of LangChain messages for prompt injection."""
        return [m for pair in self._turns for m in pair]

    def clear(self) -> None:
        """Clear the sliding window buffer (used on new session)."""
        self._turns = []

    def get_history(self) -> List[Dict[str, str]]:
        """Return raw turn exchanges for debugging and UI display."""
        return [
            {"user": str(user_msg.content), "assistant": str(ai_msg.content)}
            for user_msg, ai_msg in self._turns
        ]

    def __len__(self) -> int:
        return len(self._turns)
