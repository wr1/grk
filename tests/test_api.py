import pytest
from unittest.mock import AsyncMock, Mock
from grk.core.api import call_grok
from grk.utils.utils import GrkException


class MockAsyncIterator:
    def __init__(self, items):
        self.items = items[:]

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


@pytest.mark.asyncio
async def test_call_grok_api_failure(mocker):
    """Test API call failure handling in call_grok."""
    mock_client = mocker.Mock()
    mock_client.chat = mocker.Mock()  # Mock the chat attribute
    mock_client.chat.create.side_effect = Exception(
        "API error"
    )  # Mock the create method
    mocker.patch(
        "grk.core.api.AsyncClient", return_value=mock_client

    )  # Patch AsyncClient to return the mock

    messages = [
        {"role": "system", "content": "python-programmer"},
        {"role": "user", "content": "Test content"},
        {"role": "user", "content": "Test prompt"},
    ]
    with pytest.raises(GrkException) as exc_info:
        await call_grok(messages, "grok-3", "dummy_key")
    assert "API request failed" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("non_str", [123])
async def test_call_grok_non_string_response(mocker, non_str):
    """Test API call with non-string response content."""
    mock_client = mocker.Mock()
    mock_client.chat = mocker.Mock()
    mock_chat = mocker.Mock()
    mock_sample = mocker.Mock()
    mock_sample.content = non_str

    # Mock the stream as a callable that returns an async iterable
    mock_chat.stream = mocker.Mock(return_value=MockAsyncIterator([(Mock(), mock_sample)]))

    mock_client.chat.create.return_value = mock_chat
    mocker.patch("grk.core.api.AsyncClient", return_value=mock_client)

    messages = [{"role": "system", "content": "test"}]
    with pytest.raises(GrkException) as exc_info:
        await call_grok(messages, "grok-3", "dummy_key")
    assert "API response is not a string" in str(exc_info.value)
