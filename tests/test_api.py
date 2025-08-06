import pytest
import click
from grk.api import call_grok

def test_call_grok_api_failure(mocker):
    """Test API call failure handling in call_grok."""
    mock_client = mocker.Mock()
    mock_client.chat = mocker.Mock()  # Mock the chat attribute
    mock_client.chat.create.side_effect = Exception("API error")  # Mock the create method
    mocker.patch('grk.api.Client', return_value=mock_client)  # Patch Client to return the mock

    messages = [
        {"role": "system", "content": "python-programmer"},
        {"role": "user", "content": "Test content"},
        {"role": "user", "content": "Test prompt"},
    ]
    with pytest.raises(click.ClickException) as exc_info:
        call_grok(messages, "grok-3", "dummy_key")
    assert "API request failed" in str(exc_info.value)



