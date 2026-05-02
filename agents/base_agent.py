import json
import logging
from abc import ABC
from datetime import datetime
from pathlib import Path
from langchain.agents import create_agent
from langchain.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

_EXPERIMENT_DIR: Path = Path("data/output")
_CONTEXT_SUBDIR: str = ""

# ── Per-run token counter ─────────────────────────────────────────────────────
_run_tokens: dict = {"input": 0, "output": 0}


def reset_run_tokens() -> None:
    _run_tokens["input"] = 0
    _run_tokens["output"] = 0


def get_run_tokens() -> dict:
    total = _run_tokens["input"] + _run_tokens["output"]
    return {"input": _run_tokens["input"], "output": _run_tokens["output"], "total": total}


def _count(msg) -> None:
    """Add token usage from an AIMessage to the current run's counter."""
    usage = getattr(msg, "usage_metadata", None) or {}
    _run_tokens["input"]  += usage.get("input_tokens",  0)
    _run_tokens["output"] += usage.get("output_tokens", 0)


def set_experiment_dir(path: Path) -> None:
    """Set the experiment directory. Called once from main.py."""
    global _EXPERIMENT_DIR
    _EXPERIMENT_DIR = path


def set_context_subdir(subdir: str) -> None:
    """Set the context subfolder (e.g. 'session0', 'patient_1'). Called per session."""
    global _CONTEXT_SUBDIR
    _CONTEXT_SUBDIR = subdir


class BaseAgent(ABC):
    def __init__(self, name: str, role: str, system_prompt: str, llm, tools=None):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = llm
        self.tools = tools or []
        self.messages = []
        self._call_index = 0
        self.agent = self.setup_agent()

    def setup_agent(self):
        return create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=SystemMessage(content=self.system_prompt)
        )

    def respond(self, message: str) -> str:
        """Generate a response to a message."""
        self.messages.append({"role": "user", "content": message})
        result = self.agent.invoke({"messages": self.messages})
        last = result["messages"][-1]
        _count(last)
        response = last.content
        self.messages = result["messages"]
        self.log_response(message, response)
        return response

    def reset_memory(self):
        """Clear conversation history."""
        self.messages = []

    def log_response(self, input_msg: str, response: str, output: dict | list | str | None = None):
        self._write_context(input_msg, response, output)
        self._call_index += 1

    def _write_context(self, input_msg: str, response: str, output: dict | list | str | None = None):
        context_dir = _EXPERIMENT_DIR / "context" / _CONTEXT_SUBDIR if _CONTEXT_SUBDIR else _EXPERIMENT_DIR / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.name}_call{self._call_index:02d}.json"
        data = {
            "meta": {
                "agent_name": self.name,
                "role":       self.role,
                "call_index": self._call_index,
                "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "messages": [
                {"role": "system",    "content": self.system_prompt},
                {"role": "user",      "content": input_msg},
                {"role": "assistant", "content": response},
            ],
            "output": output if output is not None else response,
        }
        with open(context_dir / filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def __repr__(self):
        return f"<Agent name={self.name} role={self.role}>"

    # ── Structured LLM helper ────────────────────────────────────────────────

    def _invoke_structured(self, schema, system_prompt: str, user_prompt: str):
        """Invoke the LLM with a structured output schema. Logs the call and returns parsed result or None."""
        structured_llm = self.llm.with_structured_output(schema, include_raw=True, method="function_calling")
        raw = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ])
        parsed = None
        raw_text = ""
        if isinstance(raw, dict):
            # Standard LangChain include_raw=True format: {"raw": AIMessage, "parsed": BaseModel}
            _count(raw.get("raw"))
            parsed = raw.get("parsed")
            raw_msg = raw.get("raw")
            raw_text = getattr(raw_msg, "content", "") if raw_msg else ""
        elif hasattr(raw, "model_dump"):
            # DeepSeek / open_source wrappers return the parsed model directly;
            # token counting is already done inside their _StructuredOutputWrapper.
            parsed = raw
        output = parsed.model_dump() if parsed is not None else {"parse_error": True}
        self.log_response(user_prompt, raw_text or "(no raw content)", output=output)
        return parsed

    # ── Shared formatting helpers ─────────────────────────────────────────────

    @staticmethod
    def fmt_demographics(demographics: dict) -> str:
        return "\n".join(f"  {k}: {v}" for k, v in demographics.items())

    @staticmethod
    def fmt_self_report(self_report: dict) -> str:
        lines = []
        for node, items in self_report.items():
            formatted = ", ".join(
                f"{i['key']}: {i['value']}" if isinstance(i, dict) else str(i)
                for i in items
            )
            lines.append(f"  {node}: {formatted}")
        return "\n".join(lines)

    @staticmethod
    def fmt_problematic_items(problematic_items: dict) -> str:
        lines = []
        for node, keys in problematic_items.items():
            lines.append(f"  {node}: {', '.join(keys)}")
        return "\n".join(lines) or "  (none)"

    @staticmethod
    def _fmt_issues(issues: list[dict]) -> str:
        lines = []
        for issue in issues:
            lines.append(f"  {issue['component']} / {issue['item']}: {issue['explanation']}")
        return "\n".join(lines) or "  (none)"
