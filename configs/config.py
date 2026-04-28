import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class Config:
    """Configuration for all model providers"""

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


    # Lab API (Tailscale)
    LAB_API_KEY = os.getenv("LAB_API_KEY", "")
    LAB_API_URL = os.getenv("LAB_API_URL", "http://100.110.96.82:8000/chat")

    @classmethod
    def ollama_url(cls) -> str:
        return f"http://{cls.OLLAMA_IP}:{cls.OLLAMA_PORT}"

    # Deepseek
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Model definitions with their providers
MODELS = {
    # OpenAI
    "gpt-4o-mini": "openai",
    "gpt-5.4-mini": "openai",
    "gpt-5.4": "openai",

    # Anthropic
    "claude-sonnet-4-5":        "anthropic",
    "claude-haiku-4-5":         "anthropic",

    # Gemini
    "gemini-2.5-flash":       "gemini",
    "gemini-2.5-pro":         "gemini",

    # Lab API (Tailscale)
    "llama3.1-8b":  "open_source",
    "llama3.1-70b": "open_source",
    "qwen2.5-32b":  "open_source",

    # DeepSeek
    "deepseek-chat":     "deepseek",
    "deepseek-reasoner": "deepseek",
}


def get_model_provider(model_name: str) -> str | None:
    """Get the provider for a given model, or None if unknown."""
    return MODELS.get(model_name)
