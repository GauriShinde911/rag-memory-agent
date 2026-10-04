import json
import re
import logging
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from app.memory.long_term import LongTermMemory
from app.llm import text_of, invoke_with_retry, get_llm

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """You maintain the long-term memory of a personal assistant.
You get the user's latest message, the assistant's reply, and existing memories (with ids).
Return ONLY JSON: {{"ops": [...]}} where each op is one of:
{{"op":"add","text":"<self-contained fact>"}}
{{"op":"update","id":"<existing id>","text":"<corrected fact>"}}
{{"op":"delete","id":"<existing id>"}}

Rules:
- Store durable facts about the user, their projects, preferences, deadlines, and findings the user asked to be saved.
- Write facts as self-contained statements, e.g. "User's GPU budget is $80 per month."
- If the user corrects or changes something an existing memory states, emit `update` for that id (do NOT add a duplicate).
- Ignore greetings, questions, and chit-chat. If nothing should change, return {{"ops": []}}.

Existing memories:
{memories}

User message: {user}
Assistant reply: {reply}
JSON:"""


class MemoryOp(BaseModel):
    op: str = Field(description="Operation type: add, update, or delete")
    id: Optional[str] = Field(default=None, description="Memory ID for update/delete")
    text: Optional[str] = Field(default=None, description="Fact content for add/update")
    reason: Optional[str] = Field(default=None, description="Explanation if skipped or failed")


class MemoryOpsContainer(BaseModel):
    ops: List[MemoryOp] = []


class MemoryOpsResult(BaseModel):
    applied: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    raw_output: Optional[str] = None


def format_memories_for_prompt(mems: List[Dict[str, Any]]) -> str:
    """Format list of retrieved memories for updater prompt."""
    if not mems:
        return "(none)"
    lines = []
    for m in mems:
        mid = m.get("id") or "no-id"
        text = m.get("text") or ""
        lines.append(f"[{mid}] {text}")
    return "\n".join(lines)


class MemoryUpdater:
    """Adapts long-term memory via LLM feedback loop."""

    def __init__(self, llm=None):
        self.llm = llm

    def _get_llm(self):
        return self.llm or get_llm(temperature=0.0)

    def adapt(
        self,
        ltm: LongTermMemory,
        user_msg: str,
        reply: str,
        retrieved_mems: List[Dict[str, Any]],
        session_id: str = "na",
    ) -> MemoryOpsResult:
        """Run feedback loop to extract and apply memory mutations."""
        valid_ids: Set[str] = {
            m["id"] for m in retrieved_mems if m.get("id") is not None
        }
        memories_str = format_memories_for_prompt(retrieved_mems)
        prompt_text = EXTRACT_PROMPT.format(
            memories=memories_str,
            user=user_msg,
            reply=reply,
        )

        applied: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        raw_text = ""

        try:
            llm_instance = self._get_llm()
            resp = invoke_with_retry(llm_instance.invoke, prompt_text)
            raw_text = text_of(resp.content if hasattr(resp, "content") else resp)
        except Exception as e:
            logger.warning(f"Memory updater LLM call failed: {type(e).__name__}: {e}")
            skipped.append({
                "op": "error",
                "reason": f"LLM error: {type(e).__name__}: {e}",
            })
            return MemoryOpsResult(applied=applied, skipped=skipped, raw_output=raw_text)

        # Parse JSON block
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not json_match:
            logger.warning(f"Memory updater produced non-JSON output: {raw_text[:150]}")
            skipped.append({
                "op": "error",
                "reason": "No JSON block found in LLM response",
                "raw": raw_text[:200],
            })
            return MemoryOpsResult(applied=applied, skipped=skipped, raw_output=raw_text)

        try:
            data = json.loads(json_match.group(0))
            container = MemoryOpsContainer(**data)
        except Exception as e:
            logger.warning(f"Memory updater JSON validation failed: {e}")
            skipped.append({
                "op": "error",
                "reason": f"Invalid JSON structure: {e}",
                "raw": json_match.group(0)[:200],
            })
            return MemoryOpsResult(applied=applied, skipped=skipped, raw_output=raw_text)

        for item in container.ops:
            kind = (item.op or "").lower().strip()
            text_val = (item.text or "").strip()
            target_id = (item.id or "").strip()

            if kind == "add":
                if not text_val:
                    skipped.append({"op": "add", "reason": "Missing text for add operation"})
                    continue
                new_id = ltm.add(text_val, session_id=session_id)
                applied.append({"op": "add", "id": new_id, "text": text_val})

            elif kind == "update":
                if not target_id:
                    skipped.append({"op": "update", "text": text_val, "reason": "Missing target ID"})
                    continue
                if target_id not in valid_ids:
                    logger.warning(
                        f"Skipping update for id '{target_id}': not in retrieved memories {valid_ids}"
                    )
                    skipped.append({
                        "op": "update",
                        "id": target_id,
                        "text": text_val,
                        "reason": f"Target ID '{target_id}' was not in retrieved memories",
                    })
                    continue
                if not text_val:
                    skipped.append({
                        "op": "update",
                        "id": target_id,
                        "reason": "Missing replacement text",
                    })
                    continue
                res_id = ltm.update(target_id, text_val, session_id=session_id)
                if res_id:
                    applied.append({"op": "update", "id": res_id, "text": text_val})
                else:
                    skipped.append({
                        "op": "update",
                        "id": target_id,
                        "text": text_val,
                        "reason": f"ID '{target_id}' not found in database",
                    })

            elif kind == "delete":
                if not target_id:
                    skipped.append({"op": "delete", "reason": "Missing target ID"})
                    continue
                if target_id not in valid_ids:
                    logger.warning(
                        f"Skipping delete for id '{target_id}': not in retrieved memories {valid_ids}"
                    )
                    skipped.append({
                        "op": "delete",
                        "id": target_id,
                        "reason": f"Target ID '{target_id}' was not in retrieved memories",
                    })
                    continue
                res_id = ltm.delete(target_id)
                if res_id:
                    applied.append({"op": "delete", "id": res_id, "text": ""})
                else:
                    skipped.append({
                        "op": "delete",
                        "id": target_id,
                        "reason": f"ID '{target_id}' not found in database",
                    })

            else:
                skipped.append({"op": kind, "reason": f"Unsupported op '{kind}'"})

        return MemoryOpsResult(applied=applied, skipped=skipped, raw_output=raw_text)
