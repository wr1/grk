"""API interaction with Grok LLM."""

import asyncio
from typing import List, Union

from xai_sdk import AsyncClient
from xai_sdk.chat import assistant, system, user
from ..utils.utils import GrkException


async def call_grok(
    messages: List[Union[system, user, assistant]],
    model: str,
    api_key: str,
    temperature: float = 0,
) -> str:
    """Call Grok API with streaming, accumulating full response per xai-sdk patterns."""
    try:
        client = AsyncClient(api_key=api_key)
        chat = client.chat.create(
            model=model,
            temperature=temperature,
            messages=messages,
            stream=False,
        )
        full_content = ""
        async for response, chunk in chat.stream():
            if chunk.content:
                if not isinstance(chunk.content, str):
                    raise GrkException("API response is not a string")
                full_content += chunk.content
        if not full_content:
            raise ValueError("No content received from API")
        return full_content
    except Exception as e:
        raise GrkException(f"API request failed: {str(e)}")
