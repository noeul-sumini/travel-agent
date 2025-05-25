import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_create_event(calendar_tool):
    """Test creating a calendar event."""
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    result = await calendar_tool._arun(
        summary="Test Event",
        description="This is a test event",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        location="Tokyo",
        attendees=["test@example.com"]
    )
    
    assert result["status"] == "success"
    assert "event_id" in result["data"]
    assert result["data"]["summary"] == "Test Event"
    assert result["data"]["description"] == "This is a test event"

@pytest.mark.asyncio
async def test_get_event(calendar_tool):
    """Test getting a calendar event."""
    # First create an event
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    create_result = await calendar_tool._arun(
        summary="Test Event",
        description="This is a test event",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        location="Tokyo",
        attendees=["test@example.com"]
    )
    
    # Then get it
    result = await calendar_tool._arun(
        event_id=create_result["data"]["event_id"]
    )
    
    assert result["status"] == "success"
    assert result["data"]["summary"] == "Test Event"
    assert result["data"]["description"] == "This is a test event"

@pytest.mark.asyncio
async def test_update_event(calendar_tool):
    """Test updating a calendar event."""
    # First create an event
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    create_result = await calendar_tool._arun(
        summary="Test Event",
        description="This is a test event",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        location="Tokyo",
        attendees=["test@example.com"]
    )
    
    # Then update it
    new_end_time = end_time + timedelta(hours=1)
    result = await calendar_tool._arun(
        event_id=create_result["data"]["event_id"],
        summary="Updated Test Event",
        description="This is an updated test event",
        end_time=new_end_time.isoformat()
    )
    
    assert result["status"] == "success"
    assert result["data"]["summary"] == "Updated Test Event"
    assert result["data"]["description"] == "This is an updated test event"

@pytest.mark.asyncio
async def test_delete_event(calendar_tool):
    """Test deleting a calendar event."""
    # First create an event
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    create_result = await calendar_tool._arun(
        summary="Test Event",
        description="This is a test event",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        location="Tokyo",
        attendees=["test@example.com"]
    )
    
    # Then delete it
    result = await calendar_tool._arun(
        event_id=create_result["data"]["event_id"],
        delete=True
    )
    
    assert result["status"] == "success"
    
    # Verify it's deleted
    get_result = await calendar_tool._arun(
        event_id=create_result["data"]["event_id"]
    )
    assert get_result["status"] == "error"
    assert "Event not found" in get_result["error"]

@pytest.mark.asyncio
async def test_invalid_event_id(calendar_tool):
    """Test getting an invalid event."""
    result = await calendar_tool._arun(
        event_id="invalid_event_id"
    )
    
    assert result["status"] == "error"
    assert "Event not found" in result["error"] 