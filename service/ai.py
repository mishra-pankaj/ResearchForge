import os
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            temperature=0,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")