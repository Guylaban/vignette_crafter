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

    # Deepseek
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Model definitions with their providers
MODELS = {
    # OpenAI
    "gpt-4o-mini":  "openai",
    "gpt-4.1":      "openai",
    "gpt-5.4-mini": "openai",
    "gpt-5.4":      "openai",
    "gpt-5":        "openai",

    # Anthropic
    "claude-opus-4-7":          "anthropic",
    "claude-opus-4-6":          "anthropic",
    "claude-opus-4-5":          "anthropic",
    "claude-opus-4-5-20251101": "anthropic",
    "claude-opus-4-1-20250805": "anthropic",
    "claude-sonnet-4-6":        "anthropic",
    "claude-sonnet-4-5-20250929": "anthropic",
    "claude-haiku-4-5":         "anthropic",

    # Gemini
    "gemini-2.5-flash":       "gemini",
    "gemini-2.5-pro":         "gemini",

    # Lab API (Tailscale)
    "llama3.1-8b":       "open_source",
    "llama3.1-70b":      "open_source",
    "qwen2.5-32b":       "open_source",
    "qwen2.5-72b":       "open_source",
    "qwen3.6-35b":       "open_source",
    "qwen3.6-35b-ablit": "open_source",
    "gpt-oss-20b":       "open_source",
    "gemma4-31b":        "open_source",
    "nemotron-70b":      "open_source",

    # DeepSeek
    "deepseek-chat":     "deepseek",
    "deepseek-reasoner": "deepseek",
    "deepseek-v4-pro":   "deepseek",
    "deepseek-v4-flash": "deepseek",
}


def get_model_provider(model_name: str) -> str | None:
    """Get the provider for a given model, or None if unknown."""
    return MODELS.get(model_name)
