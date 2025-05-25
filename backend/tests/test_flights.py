import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_search_flights(flights_tool):
    """Test searching for flights."""
    start_date = datetime.now() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    result = await flights_tool._arun(
        origin="NRT",  # Tokyo Narita
        destination="ICN",  # Seoul Incheon
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        adults=1,
        cabin_class="economy"
    )
    
    assert result["status"] == "success"
    assert "flights" in result["data"]
    assert len(result["data"]["flights"]) > 0
    assert "airline" in result["data"]["flights"][0]
    assert "price" in result["data"]["flights"][0]
    assert "departure_time" in result["data"]["flights"][0]
    assert "arrival_time" in result["data"]["flights"][0]

@pytest.mark.asyncio
async def test_get_flight_details(flights_tool):
    """Test getting details for a specific flight."""
    # First search for flights
    start_date = datetime.now() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    search_result = await flights_tool._arun(
        origin="NRT",
        destination="ICN",
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        adults=1,
        cabin_class="economy"
    )
    
    # Then get details for the first flight
    flight_id = search_result["data"]["flights"][0]["flight_id"]
    result = await flights_tool._arun(
        flight_id=flight_id
    )
    
    assert result["status"] == "success"
    assert "airline" in result["data"]
    assert "flight_number" in result["data"]
    assert "departure" in result["data"]
    assert "arrival" in result["data"]
    assert "price" in result["data"]
    assert "available_seats" in result["data"]

@pytest.mark.asyncio
async def test_invalid_airport_code(flights_tool):
    """Test searching with invalid airport code."""
    start_date = datetime.now() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    result = await flights_tool._arun(
        origin="INVALID",
        destination="ICN",
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        adults=1,
        cabin_class="economy"
    )
    
    assert result["status"] == "error"
    assert "Invalid airport code" in result["error"]

@pytest.mark.asyncio
async def test_past_date(flights_tool):
    """Test searching for flights in the past."""
    start_date = datetime.now() - timedelta(days=1)
    end_date = start_date + timedelta(days=2)
    
    result = await flights_tool._arun(
        origin="NRT",
        destination="ICN",
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        adults=1,
        cabin_class="economy"
    )
    
    assert result["status"] == "error"
    assert "Cannot search for flights in the past" in result["error"]

@pytest.mark.asyncio
async def test_invalid_cabin_class(flights_tool):
    """Test searching with invalid cabin class."""
    start_date = datetime.now() + timedelta(days=7)
    end_date = start_date + timedelta(days=2)
    
    result = await flights_tool._arun(
        origin="NRT",
        destination="ICN",
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        adults=1,
        cabin_class="invalid_class"
    )
    
    assert result["status"] == "error"
    assert "Invalid cabin class" in result["error"] 