import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_create_travel_plan(travel_planning_tool, sample_travel_plan):
    """Test creating a travel plan."""
    result = await travel_planning_tool._arun(
        destination=sample_travel_plan["destination"],
        start_date=sample_travel_plan["start_date"],
        end_date=sample_travel_plan["end_date"],
        preferences=sample_travel_plan
    )
    
    assert result["status"] == "success"
    assert result["data"]["destination"] == sample_travel_plan["destination"]
    assert len(result["data"]["activities"]) == len(sample_travel_plan["activities"])
    assert len(result["data"]["accommodations"]) == len(sample_travel_plan["accommodations"])

@pytest.mark.asyncio
async def test_invalid_dates(travel_planning_tool):
    """Test creating a travel plan with invalid dates."""
    result = await travel_planning_tool._arun(
        destination="Tokyo",
        start_date=datetime.now().isoformat(),
        end_date=(datetime.now() - timedelta(days=1)).isoformat()
    )
    
    assert result["status"] == "error"
    assert "Start date must be before end date" in result["error"]

def test_get_plan(travel_planning_tool, sample_travel_plan):
    """Test retrieving a travel plan."""
    # First create a plan
    plan_id = f"{sample_travel_plan['destination']}_{sample_travel_plan['start_date']}_{sample_travel_plan['end_date']}"
    travel_planning_tool._run(
        destination=sample_travel_plan["destination"],
        start_date=sample_travel_plan["start_date"],
        end_date=sample_travel_plan["end_date"],
        preferences=sample_travel_plan
    )
    
    # Then retrieve it
    result = travel_planning_tool.get_plan(plan_id)
    assert result is not None
    assert result["status"] == "success"
    assert result["data"]["destination"] == sample_travel_plan["destination"]

def test_update_plan(travel_planning_tool, sample_travel_plan):
    """Test updating a travel plan."""
    # First create a plan
    plan_id = f"{sample_travel_plan['destination']}_{sample_travel_plan['start_date']}_{sample_travel_plan['end_date']}"
    travel_planning_tool._run(
        destination=sample_travel_plan["destination"],
        start_date=sample_travel_plan["start_date"],
        end_date=sample_travel_plan["end_date"],
        preferences=sample_travel_plan
    )
    
    # Then update it
    updates = {
        "activities": [
            {
                "name": "Visit Tokyo Skytree",
                "description": "Visit the tallest structure in Japan",
                "start_time": (datetime.now() + timedelta(days=8, hours=10)).isoformat(),
                "end_time": (datetime.now() + timedelta(days=8, hours=12)).isoformat(),
                "location": "Tokyo Skytree"
            }
        ]
    }
    
    result = travel_planning_tool.update_plan(plan_id, updates)
    assert result is not None
    assert result["status"] == "success"
    assert len(result["data"]["activities"]) == 1
    assert result["data"]["activities"][0]["name"] == "Visit Tokyo Skytree"

def test_delete_plan(travel_planning_tool, sample_travel_plan):
    """Test deleting a travel plan."""
    # First create a plan
    plan_id = f"{sample_travel_plan['destination']}_{sample_travel_plan['start_date']}_{sample_travel_plan['end_date']}"
    travel_planning_tool._run(
        destination=sample_travel_plan["destination"],
        start_date=sample_travel_plan["start_date"],
        end_date=sample_travel_plan["end_date"],
        preferences=sample_travel_plan
    )
    
    # Then delete it
    result = travel_planning_tool.delete_plan(plan_id)
    assert result is True
    
    # Verify it's deleted
    assert travel_planning_tool.get_plan(plan_id) is None 