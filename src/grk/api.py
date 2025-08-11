"""API interaction with Grok LLM."""

from typing import List, Union

from xai_sdk import Client
from xai_sdk.chat import assistant, system, user
import rich_click as click


def call_grok(
    messages: List[Union[system, user, assistant]],
    model: str,
    api_key: str,
    temperature: float = 0,
) -> str:
    """Call Grok API with a list of messages using recommended SDK pattern."""
    try:
        client = Client(api_key=api_key)
        chat = client.chat.create(
            model=model,
            temperature=temperature,
        )
        for msg in messages:
            chat.append(msg)
        response = chat.sample()
        if not isinstance(response.content, str):
            raise ValueError("API response is not a string")
        return response.content
    except Exception as e:
        raise click.ClickException(f"API request failed: {str(e)}")
