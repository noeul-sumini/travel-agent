import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_get_directions(maps_tool):
    """Test getting directions between two points."""
    result = await maps_tool._arun(
        origin="Tokyo Station",
        destination="Tokyo Skytree",
        mode="transit"
    )
    
    assert result["status"] == "success"
    assert "distance" in result["data"]
    assert "duration" in result["data"]
    assert "steps" in result["data"]
    assert len(result["data"]["steps"]) > 0

@pytest.mark.asyncio
async def test_get_place_details(maps_tool):
    """Test getting details for a place."""
    result = await maps_tool._arun(
        place_id="ChIJ51cu8IcbXWARiRtXIothAS4",  # Tokyo Skytree
        fields=["name", "formatted_address", "rating", "opening_hours"]
    )
    
    assert result["status"] == "success"
    assert "name" in result["data"]
    assert "formatted_address" in result["data"]
    assert "rating" in result["data"]
    assert "opening_hours" in result["data"]

@pytest.mark.asyncio
async def test_search_places(maps_tool):
    """Test searching for places."""
    result = await maps_tool._arun(
        query="restaurants in Tokyo",
        location="35.6762,139.6503",  # Tokyo coordinates
        radius=5000
    )
    
    assert result["status"] == "success"
    assert "places" in result["data"]
    assert len(result["data"]["places"]) > 0
    assert "name" in result["data"]["places"][0]
    assert "place_id" in result["data"]["places"][0]

@pytest.mark.asyncio
async def test_invalid_place_id(maps_tool):
    """Test getting details for invalid place ID."""
    result = await maps_tool._arun(
        place_id="invalid_place_id",
        fields=["name", "formatted_address"]
    )
    
    assert result["status"] == "error"
    assert "Place not found" in result["error"]

@pytest.mark.asyncio
async def test_invalid_transport_mode(maps_tool):
    """Test getting directions with invalid transport mode."""
    result = await maps_tool._arun(
        origin="Tokyo Station",
        destination="Tokyo Skytree",
        mode="invalid_mode"
    )
    
    assert result["status"] == "error"
    assert "Invalid transport mode" in result["error"] 