import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def query_ollama(model: str, prompt: str):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # set to True if you want tokens streamed
    }

    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()  # raise an error if something fails
    data = response.json()

    # The text result is stored under the "response" key
    return data.get("response", "")