from fastapi import APIRouter
from pydantic import BaseModel
from kv_operations import kv_put, kv_get, kv_delete, test_kv_access

kv_router = APIRouter()


class KVRequest(BaseModel):
    key_name: str
    value: str


@kv_router.put("/kv-value")
async def add_kv_value(request: KVRequest):
    val = kv_put(request.key_name, request.value)
    return {"success": val}


@kv_router.get("/kv-value/{key_name}")
async def get_kv_value(key_name: str):
    val = kv_get(key_name)
    return {"value": val}


@kv_router.delete("/kv-value/{key_name}")
async def delete_kv_value(key_name: str):
    success = kv_delete(key_name)
    return {"success": success}


@kv_router.get("/test-kv")
async def test_kv():
    test_kv_access()
