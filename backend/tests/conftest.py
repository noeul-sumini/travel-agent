import pytest
from datetime import datetime, timedelta
from app.core.agent.travel_agent import TravelAgent
from app.tools.travel_planning import TravelPlanningTool
from app.tools.weather import WeatherTool
from app.tools.maps import MapsTool
from app.tools.calendar import CalendarTool
from app.tools.flights import FlightsTool
from app.tools.budget import BudgetTool

@pytest.fixture
def travel_agent():
    """Create a TravelAgent instance for testing."""
    return TravelAgent()

@pytest.fixture
def travel_planning_tool():
    """Create a TravelPlanningTool instance for testing."""
    return TravelPlanningTool()

@pytest.fixture
def weather_tool():
    """Create a WeatherTool instance for testing."""
    return WeatherTool()

@pytest.fixture
def maps_tool():
    """Create a MapsTool instance for testing."""
    return MapsTool()

@pytest.fixture
def calendar_tool():
    """Create a CalendarTool instance for testing."""
    return CalendarTool()

@pytest.fixture
def flights_tool():
    """Create a FlightsTool instance for testing."""
    return FlightsTool()

@pytest.fixture
def budget_tool():
    """Create a BudgetTool instance for testing."""
    return BudgetTool()

@pytest.fixture
def sample_travel_plan():
    """Create a sample travel plan for testing."""
    return {
        "destination": "Tokyo",
        "start_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "activities": [
            {
                "name": "Visit Tokyo Tower",
                "description": "Visit the iconic Tokyo Tower",
                "start_time": (datetime.now() + timedelta(days=7, hours=10)).isoformat(),
                "end_time": (datetime.now() + timedelta(days=7, hours=12)).isoformat(),
                "location": "Tokyo Tower"
            }
        ],
        "accommodations": [
            {
                "name": "Tokyo Hotel",
                "check_in": (datetime.now() + timedelta(days=7)).isoformat(),
                "check_out": (datetime.now() + timedelta(days=14)).isoformat(),
                "location": "Tokyo"
            }
        ],
        "transportation": [
            {
                "type": "flight",
                "from": "Seoul",
                "to": "Tokyo",
                "departure": (datetime.now() + timedelta(days=7, hours=8)).isoformat(),
                "arrival": (datetime.now() + timedelta(days=7, hours=10)).isoformat()
            }
        ],
        "budget": {
            "total": 2000.0,
            "currency": "USD",
            "breakdown": {
                "accommodation": 1000.0,
                "transportation": 500.0,
                "activities": 300.0,
                "food": 200.0
            }
        }
    }

@pytest.fixture
def sample_budget():
    """Create a sample budget for testing."""
    return {
        "total_budget": 2000.0,
        "base_currency": "USD",
        "start_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "items": [
            {
                "category": "accommodation",
                "amount": 1000.0,
                "currency": "USD",
                "date": (datetime.now() + timedelta(days=7)).isoformat(),
                "description": "Hotel booking"
            }
        ]
    } 