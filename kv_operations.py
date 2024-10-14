import os
import httpx
import requests
from dotenv import load_dotenv

load_dotenv()

KV_AUTH = os.getenv("KV_AUTH")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
NAMESPACE_ID = os.getenv("NAMESPACE_ID")
KV_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{NAMESPACE_ID}"


async def kv_put(key_name: str, value: str) -> bool:
    headers = {
        "Authorization": f"Bearer {KV_AUTH}",
        "Content-Type": "text/plain",
    }
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{KV_URL}/values/{key_name}", headers=headers, content=value
        )
    return response.status_code == 200


async def kv_get(key_name: str) -> str:
    headers = {
        "Content-Type": "*/*",
        "Authorization": f"Bearer {KV_AUTH}",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{KV_URL}/values/{key_name}", headers=headers)
    if response.status_code == 200:
        return response.text
    return ""


def kv_delete(key_name: str) -> bool:
    headers = {
        "Authorization": f"Bearer {KV_AUTH}",
    }
    response = requests.delete(f"{KV_URL}/values/{key_name}", headers=headers)
    print(response)
    return response.status_code == 200


def test_kv_access() -> None:
    url = f"{KV_URL}"
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
