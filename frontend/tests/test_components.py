import pytest
from datetime import datetime, timedelta
from app.components.TravelPlan import (
    format_date,
    format_time,
    format_currency,
    display_activities,
    display_accommodations,
    display_transportation,
    display_budget
)
from app.components.Preferences import (
    get_date_range,
    get_budget_range,
    get_accommodation_type,
    get_travel_style
)
from app.components.Chat import (
    display_chat_message,
    display_chat_history,
    handle_user_input
)

# Test data
SAMPLE_ACTIVITY = {
    "name": "City Tour",
    "description": "Guided tour of the city",
    "location": "Downtown",
    "start_time": "2024-03-20T10:00:00",
    "end_time": "2024-03-20T12:00:00"
}

SAMPLE_ACCOMMODATION = {
    "name": "Grand Hotel",
    "location": "123 Main St",
    "check_in": "2024-03-20",
    "check_out": "2024-03-25"
}

SAMPLE_TRANSPORT = {
    "type": "flight",
    "from": "Seoul",
    "to": "Tokyo",
    "departure": "2024-03-20T08:00:00",
    "arrival": "2024-03-20T10:00:00"
}

SAMPLE_BUDGET = {
    "total": 5000,
    "currency": "USD",
    "breakdown": {
        "accommodation": 2000,
        "transportation": 1000,
        "activities": 1500,
        "food": 500
    }
}

def test_format_date():
    """Test date formatting."""
    date_str = "2024-03-20"
    assert format_date(date_str) == "2024-03-20"

def test_format_time():
    """Test time formatting."""
    time_str = "2024-03-20T10:00:00"
    assert format_time(time_str) == "10:00"

def test_format_currency():
    """Test currency formatting."""
    assert format_currency(1000.50, "USD") == "USD 1,000.50"
    assert format_currency(5000, "EUR") == "EUR 5,000.00"

def test_display_activities(capsys):
    """Test activities display."""
    display_activities([SAMPLE_ACTIVITY])
    captured = capsys.readouterr()
    assert "City Tour" in captured.out
    assert "Guided tour" in captured.out

def test_display_accommodations(capsys):
    """Test accommodations display."""
    display_accommodations([SAMPLE_ACCOMMODATION])
    captured = capsys.readouterr()
    assert "Grand Hotel" in captured.out
    assert "123 Main St" in captured.out

def test_display_transportation(capsys):
    """Test transportation display."""
    display_transportation([SAMPLE_TRANSPORT])
    captured = capsys.readouterr()
    assert "Seoul" in captured.out
    assert "Tokyo" in captured.out

def test_display_budget(capsys):
    """Test budget display."""
    display_budget(SAMPLE_BUDGET)
    captured = capsys.readouterr()
    assert "USD 5,000.00" in captured.out
    assert "accommodation" in captured.out

def test_get_date_range():
    """Test date range selection."""
    start_date, end_date = get_date_range()
    assert isinstance(start_date, datetime)
    assert isinstance(end_date, datetime)
    assert end_date > start_date

def test_get_budget_range():
    """Test budget range selection."""
    min_budget, max_budget = get_budget_range()
    assert isinstance(min_budget, int)
    assert isinstance(max_budget, int)
    assert min_budget <= max_budget

def test_get_accommodation_type():
    """Test accommodation type selection."""
    acc_type = get_accommodation_type()
    assert acc_type in ["Hotel", "Hostel", "Apartment", "Resort"]

def test_get_travel_style():
    """Test travel style selection."""
    styles = get_travel_style()
    assert isinstance(styles, list)
    valid_styles = ["Adventure", "Relaxation", "Cultural", "Food & Wine", "Shopping", "Nature"]
    assert all(style in valid_styles for style in styles)

def test_display_chat_message(capsys):
    """Test chat message display."""
    message = {"role": "user", "content": "Hello"}
    display_chat_message(message)
    captured = capsys.readouterr()
    assert "Hello" in captured.out

def test_display_chat_history(capsys):
    """Test chat history display."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    display_chat_history(messages)
    captured = capsys.readouterr()
    assert "Hello" in captured.out
    assert "Hi there!" in captured.out 