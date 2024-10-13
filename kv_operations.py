import os
import requests
from dotenv import load_dotenv

load_dotenv()

KV_AUTH = os.getenv("KV_AUTH")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
NAMESPACE_ID = os.getenv("NAMESPACE_ID")
KV_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{NAMESPACE_ID}"


def kv_put(key: str, value: str) -> bool:
    headers = {
        "Authorization": f"Bearer {KV_AUTH}",
        "Content-Type": "text/plain",
    }
    response = requests.put(f"{KV_URL}/{key}", headers=headers, data=value)
    return response.status_code == 200


def kv_get(key: str) -> str:
    headers = {
        "Authorization": f"Bearer {KV_AUTH}",
    }
    response = requests.get(f"{KV_URL}/{key}", headers=headers)
    if response.status_code == 200:
        return response.text
    return ""


def test_kv_access() -> None:
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{NAMESPACE_ID}"
    headers = {
        "Authorization": f"Bearer {KV_AUTH}",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(data)
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")
