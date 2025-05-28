import click
import json
import requests
import numpy as np
from pathlib import Path

API_URL = "https://api.x.ai/v1/chat/completions"


def vectorize_text(text: str) -> np.ndarray:
    """Convert text to a simple vector using ASCII values."""
    return np.array([ord(c) for c in text[:100]], dtype=np.float32)


def call_grok(cfold: str, prompt: str, model: str, api_key: str) -> str:
    """Send cfold and prompt to Grok LLM and return response."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "you are an expert python programmer, writing clean code",
            },
            {"role": "user", "content": cfold + "\n" + prompt},
        ],
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


@click.command()
@click.argument("cfold", type=click.Path(exists=True))
@click.option("-p", "--prompt", default="", help="Additional prompt text")
@click.option("-o", "--output", default="output.txt", help="Output cfold file")
@click.option("-j", "--json-out", default="output.json", help="Output JSON file")
@click.option("-m", "--model", default="grok-3-mini", help="Grok model to use")
@click.option(
    "-k", "--api-key", required=True, envvar="XAI_API_KEY", help="xAI API key"
)
def main(cfold: str, prompt: str, output: str, json_out: str, model: str, api_key: str):
    """CLI tool to push cfold to Grok LLM and save output."""
    cfold_content = Path(cfold).read_text()
    print(api_key)

    response = call_grok(cfold_content, prompt, model, api_key)
    Path(output).write_text(f"{response}")
    json.dump(
        {"input": cfold_content, "prompt": prompt, "response": response},
        Path(json_out).open("w"),
        indent=2,
    )


if __name__ == "__main__":
    main()
