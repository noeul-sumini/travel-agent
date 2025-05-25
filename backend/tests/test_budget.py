import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_create_budget(budget_tool, sample_budget):
    """Test creating a budget."""
    result = await budget_tool._arun(
        trip_id="test_trip_1",
        currency="USD",
        items=sample_budget["items"]
    )
    
    assert result["status"] == "success"
    assert result["data"]["trip_id"] == "test_trip_1"
    assert result["data"]["currency"] == "USD"
    assert len(result["data"]["items"]) == len(sample_budget["items"])
    assert result["data"]["total_amount"] == sum(item["amount"] for item in sample_budget["items"])

@pytest.mark.asyncio
async def test_get_budget(budget_tool, sample_budget):
    """Test getting a budget."""
    # First create a budget
    await budget_tool._arun(
        trip_id="test_trip_1",
        currency="USD",
        items=sample_budget["items"]
    )
    
    # Then get it
    result = await budget_tool._arun(
        trip_id="test_trip_1"
    )
    
    assert result["status"] == "success"
    assert result["data"]["trip_id"] == "test_trip_1"
    assert result["data"]["currency"] == "USD"
    assert len(result["data"]["items"]) == len(sample_budget["items"])

@pytest.mark.asyncio
async def test_add_expense(budget_tool, sample_budget):
    """Test adding an expense to a budget."""
    # First create a budget
    await budget_tool._arun(
        trip_id="test_trip_1",
        currency="USD",
        items=sample_budget["items"]
    )
    
    # Then add an expense
    new_expense = {
        "category": "Food",
        "description": "Dinner at restaurant",
        "amount": 50.0,
        "date": datetime.now().isoformat()
    }
    
    result = await budget_tool._arun(
        trip_id="test_trip_1",
        add_expense=new_expense
    )
    
    assert result["status"] == "success"
    assert len(result["data"]["items"]) == len(sample_budget["items"]) + 1
    assert result["data"]["total_amount"] == sum(item["amount"] for item in sample_budget["items"]) + new_expense["amount"]

@pytest.mark.asyncio
async def test_update_exchange_rate(budget_tool, sample_budget):
    """Test updating exchange rates."""
    # First create a budget
    await budget_tool._arun(
        trip_id="test_trip_1",
        currency="USD",
        items=sample_budget["items"]
    )
    
    # Then update exchange rate
    result = await budget_tool._arun(
        trip_id="test_trip_1",
        update_rates=True
    )
    
    assert result["status"] == "success"
    assert "exchange_rates" in result["data"]
    assert "USD" in result["data"]["exchange_rates"]
    assert "JPY" in result["data"]["exchange_rates"]
    assert "EUR" in result["data"]["exchange_rates"]

@pytest.mark.asyncio
async def test_invalid_currency(budget_tool, sample_budget):
    """Test creating a budget with invalid currency."""
    result = await budget_tool._arun(
        trip_id="test_trip_1",
        currency="INVALID",
        items=sample_budget["items"]
    )
    
    assert result["status"] == "error"
    assert "Invalid currency code" in result["error"]

@pytest.mark.asyncio
async def test_negative_amount(budget_tool):
    """Test adding an expense with negative amount."""
    result = await budget_tool._arun(
        trip_id="test_trip_1",
        currency="USD",
        items=[{
            "category": "Food",
            "description": "Dinner",
            "amount": -50.0,
            "date": datetime.now().isoformat()
        }]
    )
    
    assert result["status"] == "error"
    assert "Amount must be positive" in result["error"] 