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
    """Call Grok API with a list of messages."""
    try:
        client = Client(api_key=api_key)
        chat = client.chat.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return chat.sample().content
    except Exception as e:
        raise click.ClickException(f"API request failed: {str(e)}")


