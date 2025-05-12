import pytest
from httpx import AsyncClient
from fastapi import status

from main import app, eventhub_client

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_send_event_success(monkeypatch):
    # Mock the send_event method to avoid real Azure calls
    async def mock_send_event(payload):
        assert payload == {"key": "value"}
        return None

    monkeypatch.setattr(eventhub_client, "send_event", mock_send_event)
    payload = {"data": {"key": "value"}}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/events", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"detail": "Event sent successfully"}

@pytest.mark.asyncio
async def test_send_event_validation_error(monkeypatch):
    # Mock to raise ValueError
    async def mock_send_event(payload):
        raise ValueError("Invalid payload")

    monkeypatch.setattr(eventhub_client, "send_event", mock_send_event)
    payload = {"data": {"key": "value"}}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/events", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid payload"

@pytest.mark.asyncio
async def test_send_event_server_error(monkeypatch):
    # Mock to raise generic Exception
    async def mock_send_event(payload):
        raise Exception("Something went wrong")

    monkeypatch.setattr(eventhub_client, "send_event", mock_send_event)
    payload = {"data": {"key": "value"}}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/events", json=payload)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Failed to send event"
