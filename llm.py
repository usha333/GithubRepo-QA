import os
from groq import Groq

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable not set. "
                "Get a free key at https://console.groq.com and run:\n"
                "  export GROQ_API_KEY='gsk_...'"
            )
        _client = Groq(api_key=api_key)
    return _client


def ask_llm(prompt: str, model: str = "openai/gpt-oss-20b", temperature: float = 0.2) -> str:
    """
    Sends a prompt to Groq and returns the text response.
    temperature is kept low (0.2) because we want grounded, factual
    answers about code, not creative variation.
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
