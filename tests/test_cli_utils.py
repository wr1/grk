"""Tests for CLI utility functions."""

import pytest


@pytest.mark.parametrize(
    "raw_response, expected_cleaned, expected_message",
    [
        ('[{"path": "file.txt"}]', '{"files": [{"path": "file.txt"}]}', ""),
        (
            'Here\'s the update: ```json\n[{"path": "file.txt"}]\n```',
            '{"files": [{"path": "file.txt"}]}',
            "Here's the update:",
        ),
        (
            'Explanatory text {"files": [{"path": "file.txt"}]}',
            '{"files": [{"path": "file.txt"}]}',
            "Explanatory text",
        ),
        ("Invalid response without JSON", "", "Invalid response without JSON"),
    ],
)
def test_postprocess_response(raw_response, expected_cleaned, expected_message):
    """Test postprocess_response function."""
    from grk.core.session import postprocess_response

    cleaned, message = postprocess_response(raw_response)
    assert cleaned.replace("\n", "") == expected_cleaned.replace(
        "\n", ""
    )  # Ignore formatting
    assert message == expected_message
