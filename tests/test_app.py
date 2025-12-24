import sys
import os
import pytest

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import urls, stats


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_create_short_link(client):
    response = client.post(
        "/shorten",
        json={
            "url": "https://example.com",
            "user_id": "test_user"
        }
    )

    assert response.status_code == 201

    data = response.get_json()
    assert "short_id" in data

    short_id = data["short_id"]
    assert short_id in urls
    assert urls[short_id]["url"] == "https://example.com"
    assert urls[short_id]["user_id"] == "test_user"


def test_redirect_and_stats(client):
    response = client.post(
        "/shorten",
        json={
            "url": "https://example.com",
            "user_id": "stats_user"
        }
    )
    short_id = response.get_json()["short_id"]

    redirect_response = client.get(f"/{short_id}")
    assert redirect_response.status_code == 302

    stats_response = client.get(f"/stats/{short_id}")
    assert stats_response.status_code == 200

    data = stats_response.get_json()
    assert data["clicks"] == 1
    assert len(data["unique_ips"]) == 1
