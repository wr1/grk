"""API interaction with Grok LLM."""

import requests
import rich_click as click

API_URL = "https://api.x.ai/v1/chat/completions"

def call_grok(
    file_content: str,
    prompt: str,
    model: str,
    api_key: str,
    system_message: str,
    temperature: float = 0,
) -> str:
    """Call Grok API with content and prompt."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": file_content + "\n" + prompt},
        ],
        "stream": False,
        "temperature": temperature,
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        raise click.ClickException(f"API request failed: {str(e)}")
