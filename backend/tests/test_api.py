import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_chat_endpoint():
    """Test chat endpoint with valid input."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "I want to plan a trip to Tokyo",
            "history": []
        }
    )
    assert response.status_code == 200
    assert "response" in response.json()

def test_chat_endpoint_invalid_input():
    """Test chat endpoint with invalid input."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "",  # Empty message
            "history": []
        }
    )
    assert response.status_code == 422  # Validation error

def test_chat_endpoint_streaming():
    """Test chat endpoint streaming response."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Plan a trip to Paris",
            "history": []
        },
        stream=True
    )
    assert response.status_code == 200
    for line in response.iter_lines():
        if line:
            assert line.startswith(b"data: ")

def test_create_travel_plan():
    """Test travel plan creation endpoint."""
    plan_data = {
        "destination": "Tokyo",
        "start_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "preferences": {
            "budget": 2000,
            "accommodation_type": "hotel",
            "travel_style": ["cultural", "food"]
        }
    }
    response = client.post("/api/v1/travel-plans", json=plan_data)
    assert response.status_code == 200
    assert "plan_id" in response.json()

def test_create_travel_plan_invalid_dates():
    """Test travel plan creation with invalid dates."""
    plan_data = {
        "destination": "Tokyo",
        "start_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=7)).isoformat(),  # End date before start date
        "preferences": {
            "budget": 2000,
            "accommodation_type": "hotel",
            "travel_style": ["cultural", "food"]
        }
    }
    response = client.post("/api/v1/travel-plans", json=plan_data)
    assert response.status_code == 400
    assert "error" in response.json()

def test_get_travel_plan():
    """Test getting a travel plan."""
    # First create a plan
    plan_data = {
        "destination": "Paris",
        "start_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "preferences": {
            "budget": 3000,
            "accommodation_type": "hotel",
            "travel_style": ["cultural", "shopping"]
        }
    }
    create_response = client.post("/api/v1/travel-plans", json=plan_data)
    plan_id = create_response.json()["plan_id"]

    # Then get the plan
    response = client.get(f"/api/v1/travel-plans/{plan_id}")
    assert response.status_code == 200
    assert response.json()["destination"] == "Paris"

def test_get_nonexistent_travel_plan():
    """Test getting a non-existent travel plan."""
    response = client.get("/api/v1/travel-plans/nonexistent-id")
    assert response.status_code == 404

def test_update_travel_plan():
    """Test updating a travel plan."""
    # First create a plan
    plan_data = {
        "destination": "London",
        "start_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "preferences": {
            "budget": 2500,
            "accommodation_type": "hotel",
            "travel_style": ["cultural"]
        }
    }
    create_response = client.post("/api/v1/travel-plans", json=plan_data)
    plan_id = create_response.json()["plan_id"]

    # Then update it
    update_data = {
        "preferences": {
            "budget": 3000,
            "accommodation_type": "apartment",
            "travel_style": ["cultural", "shopping"]
        }
    }
    response = client.put(f"/api/v1/travel-plans/{plan_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["preferences"]["budget"] == 3000

def test_delete_travel_plan():
    """Test deleting a travel plan."""
    # First create a plan
    plan_data = {
        "destination": "Rome",
        "start_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "preferences": {
            "budget": 2000,
            "accommodation_type": "hotel",
            "travel_style": ["cultural"]
        }
    }
    create_response = client.post("/api/v1/travel-plans", json=plan_data)
    plan_id = create_response.json()["plan_id"]

    # Then delete it
    response = client.delete(f"/api/v1/travel-plans/{plan_id}")
    assert response.status_code == 200

    # Verify it's deleted
    get_response = client.get(f"/api/v1/travel-plans/{plan_id}")
    assert get_response.status_code == 404

def test_calendar_integration():
    """Test calendar integration endpoint."""
    calendar_data = {
        "plan_id": "test-plan-id",
        "events": [
            {
                "title": "Flight to Tokyo",
                "start": (datetime.now() + timedelta(days=7)).isoformat(),
                "end": (datetime.now() + timedelta(days=7, hours=2)).isoformat(),
                "location": "Narita Airport"
            }
        ]
    }
    response = client.post("/api/v1/calendar/integrate", json=calendar_data)
    assert response.status_code == 200
    assert "status" in response.json()

def test_calendar_integration_invalid_data():
    """Test calendar integration with invalid data."""
    calendar_data = {
        "plan_id": "test-plan-id",
        "events": [
            {
                "title": "Invalid Event",
                "start": "invalid-date",
                "end": "invalid-date",
                "location": "Somewhere"
            }
        ]
    }
    response = client.post("/api/v1/calendar/integrate", json=calendar_data)
    assert response.status_code == 422

def test_weather_endpoint():
    """Test weather endpoint."""
    response = client.get("/api/v1/weather/Tokyo")
    assert response.status_code == 200
    assert "temperature" in response.json()
    assert "conditions" in response.json()

def test_weather_endpoint_invalid_city():
    """Test weather endpoint with invalid city."""
    response = client.get("/api/v1/weather/NonexistentCity")
    assert response.status_code == 404

def test_maps_endpoint():
    """Test maps endpoint."""
    response = client.get("/api/v1/maps/search?query=Tokyo+Tower")
    assert response.status_code == 200
    assert "results" in response.json()

def test_maps_endpoint_invalid_query():
    """Test maps endpoint with invalid query."""
    response = client.get("/api/v1/maps/search?query=")
    assert response.status_code == 400 