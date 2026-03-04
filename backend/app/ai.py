import os

from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-oss-120b"


def get_ai_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)


def ai_test() -> str:
    """Send a simple test prompt and return the AI response text."""
    client = get_ai_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "What is 2+2? Reply with just the number."}],
    )
    return response.choices[0].message.content or ""
