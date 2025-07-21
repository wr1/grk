"""API interaction with Grok LLM."""

from xai_sdk import Client
import rich_click as click
from xai_sdk.chat import system, user


def call_grok(
    file_content: str,
    prompt: str,
    model: str,
    api_key: str,
    system_message: str,
    temperature: float = 0,
) -> str:
    """Call Grok API with content and prompt."""
    try:
        client = Client(api_key=api_key)
        chat = client.chat.create(
            model=model,
            messages=[
                system(system_message),
                user(file_content),
                user(prompt),
            ],
            temperature=temperature,
        )
        return chat.sample().content
        # return chat_response.choices[0].message.content  # Extract response content
    except Exception as e:
        raise click.ClickException(f"API request failed: {str(e)}")
