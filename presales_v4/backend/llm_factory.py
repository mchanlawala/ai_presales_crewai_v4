"""
llm_factory.py
--------------
Single place to create the LLM and embedding objects.
Set  LLM_PROVIDER=openai  in .env to use OpenAI instead of Ollama.
"""
import os


def get_llm(temperature: float = 0):
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    #if provider == "openai":
    #    from langchain_openai import ChatOpenAI
    #    return ChatOpenAI(
    #        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    #        temperature=temperature,
    #        api_key=os.getenv("OPENAI_API_KEY"),
    #    )
    #else:
    #    from langchain_ollama import ChatOllama
    #    return ChatOllama(
    #        model=os.getenv("LLM_MODEL", "qwen2.5:14b"),
    #        temperature=temperature,
    #        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    #    )


def get_embeddings():
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
    #if provider == "openai":
    #    from langchain_openai import OpenAIEmbeddings
    #    return OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
    #else:
    #    from langchain_ollama import OllamaEmbeddings
    #    return OllamaEmbeddings(
    #        model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
    #        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    #    )
