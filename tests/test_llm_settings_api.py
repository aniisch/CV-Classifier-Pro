import pytest
from fastapi.testclient import TestClient

from src.services.api import app, mask_api_key
from src.database.database import SessionLocal
from src.database.models import LLMSettings


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("key,expected", [("", ""), ("short", "****"), ("sk-abcdef123456", "****3456")])
def test_mask_api_key(key, expected):
    assert mask_api_key(key) == expected


def test_get_masks_and_put_keeps_stored_key(client):
    body = {"provider": "azure_openai", "api_key": "secret-key-1234", "model": "m", "ollama_url": "u"}
    assert client.put("/api/llm-settings", json=body).json()["api_key"] == "****1234"
    masked = client.get("/api/llm-settings").json()
    assert "secret" not in str(masked)
    client.put("/api/llm-settings", json={**body, "api_key": masked["api_key"], "model": "m2"})
    db = SessionLocal()
    stored = db.query(LLMSettings).first()
    assert (stored.api_key, stored.model) == ("secret-key-1234", "m2")
    db.close()
