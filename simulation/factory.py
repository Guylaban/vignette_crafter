from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from configs.config import Config, get_model_provider
from simulation.open_source_llm import OpenSourceChatModel
from simulation.deepseek_llm import DeepSeekChatModel


def build_llm(model_name: str, temperature: float = 0.7):
    """Instantiate the right LLM class based on the model's provider."""
    provider = get_model_provider(model_name)
    if provider == "openai":
        return ChatOpenAI(model=model_name, temperature=temperature, api_key=SecretStr(Config.OPENAI_API_KEY or ""))
    if provider == "anthropic":
        # claude-opus-4-7 and newer models don't accept temperature
        NO_TEMP_MODELS = {"claude-opus-4-7"}
        kwargs = {} if model_name in NO_TEMP_MODELS else {"temperature": temperature}
        return ChatAnthropic(model_name=model_name, api_key=SecretStr(Config.ANTHROPIC_API_KEY or ""), timeout=60, stop=None, **kwargs)
    if provider == "ollama":
        return ChatOllama(model=model_name, temperature=temperature, base_url=Config.ollama_url())
    if provider == "open_source":
        return OpenSourceChatModel(model=model_name, api_url=Config.LAB_API_URL,
                            api_key=Config.LAB_API_KEY, temperature=temperature)
    if provider == "deepseek":
        return DeepSeekChatModel(model=model_name, temperature=temperature,
                                 api_key=SecretStr(Config.DEEPSEEK_API_KEY),
                                 base_url="https://api.deepseek.com")
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature,
                                      google_api_key=SecretStr(Config.GEMINI_API_KEY or ""))
    raise ValueError(f"Unknown provider for model '{model_name}'. Add it to configs/config.py.")
