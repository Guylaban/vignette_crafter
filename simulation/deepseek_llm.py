"""LangChain wrapper for DeepSeek — overrides with_structured_output to use JSON parsing."""
import json
import logging
import re
from typing import Type
from pydantic import BaseModel, SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


class _StructuredOutputWrapper:
    """Asks for JSON in the prompt and parses the response."""

    def __init__(self, llm, schema: Type[BaseModel]):
        self._llm    = llm
        self._schema = schema

    def invoke(self, messages: list, **kwargs) -> BaseModel:
        fields = list(self._schema.model_json_schema()["properties"].keys())
        json_instruction = (
            f"\nRespond with a JSON object only — no explanation, no markdown fences, no schema definition. "
            f"Fill in actual values for these fields: {fields}. "
            f"Field types for reference: {self._schema.model_json_schema()['properties']}"
        )
        augmented = list(messages)
        last = augmented[-1]
        content = last["content"] if isinstance(last, dict) else last.content
        role    = last.get("role", "user") if isinstance(last, dict) else "user"
        augmented[-1] = {"role": role, "content": content + json_instruction}

        result = self._llm.invoke(augmented)
        from agents.base_agent import _count
        _count(result)
        text  = result.content if hasattr(result, "content") else str(result)
        clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        try:
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if not match:
                logger.warning("StructuredOutputWrapper: no JSON object found. Raw text (first 300): %r", text[:300])
                return None
            data = json.loads(match.group())
            return self._schema(**data)
        except Exception as e:
            logger.warning("StructuredOutputWrapper parse failed (%s). Clean text (first 300): %r", e, clean[:300])
            return None


class DeepSeekChatModel(ChatOpenAI):
    """ChatOpenAI pointed at DeepSeek with JSON-parsing structured output."""

    def with_structured_output(self, schema: Type[BaseModel], **kwargs) -> _StructuredOutputWrapper:
        return _StructuredOutputWrapper(self, schema)
