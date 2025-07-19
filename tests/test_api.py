import pytest
import requests
import click
from grk.api import call_grok

def test_call_grok_api_failure(mocker):
    """Test API call failure handling in call_grok."""
    mock_post = mocker.patch('requests.post')
    mock_post.side_effect = requests.exceptions.RequestException("API error")

    with pytest.raises(click.ClickException) as exc_info:
        call_grok("Test content", "Test prompt", "grok-3", "dummy_key", "python-programmer")
    assert "API request failed" in str(exc_info.value)
