import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_get_weather(weather_tool):
    """Test getting current weather."""
    result = await weather_tool._arun(
        location="Tokyo",
        date=datetime.now().isoformat()
    )
    
    assert result["status"] == "success"
    assert "temperature" in result["data"]
    assert "conditions" in result["data"]
    assert "humidity" in result["data"]
    assert "wind_speed" in result["data"]

@pytest.mark.asyncio
async def test_get_forecast(weather_tool):
    """Test getting weather forecast."""
    result = await weather_tool._arun(
        location="Tokyo",
        date=(datetime.now() + timedelta(days=1)).isoformat()
    )
    
    assert result["status"] == "success"
    assert "temperature" in result["data"]
    assert "conditions" in result["data"]
    assert "humidity" in result["data"]
    assert "wind_speed" in result["data"]

@pytest.mark.asyncio
async def test_invalid_location(weather_tool):
    """Test getting weather for invalid location."""
    result = await weather_tool._arun(
        location="InvalidLocation123",
        date=datetime.now().isoformat()
    )
    
    assert result["status"] == "error"
    assert "Location not found" in result["error"]

@pytest.mark.asyncio
async def test_past_date(weather_tool):
    """Test getting weather for past date."""
    result = await weather_tool._arun(
        location="Tokyo",
        date=(datetime.now() - timedelta(days=1)).isoformat()
    )
    
    assert result["status"] == "error"
    assert "Cannot get weather for past dates" in result["error"]

@pytest.mark.asyncio
async def test_far_future_date(weather_tool):
    """Test getting weather for date too far in future."""
    result = await weather_tool._arun(
        location="Tokyo",
        date=(datetime.now() + timedelta(days=15)).isoformat()
    )
    
    assert result["status"] == "error"
    assert "Cannot get weather forecast for dates more than 14 days in the future" in result["error"] 