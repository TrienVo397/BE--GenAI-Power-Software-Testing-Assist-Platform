# filepath: fastapi-sqlmodel-backend/tests/api/v1/test_items.py

import pytest
from httpx import AsyncClient
from app.main import app
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate

@pytest.mark.asyncio
async def test_create_item():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/items/", json={"name": "Test Item", "description": "A test item"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"

@pytest.mark.asyncio
async def test_read_item():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/items/1")
    assert response.status_code == 200
    assert "name" in response.json()

@pytest.mark.asyncio
async def test_update_item():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put("/api/v1/items/1", json={"name": "Updated Item", "description": "An updated test item"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Item"

@pytest.mark.asyncio
async def test_delete_item():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete("/api/v1/items/1")
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_read_nonexistent_item():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/items/999")
    assert response.status_code == 404