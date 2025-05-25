import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

def get_date_range() -> Tuple[datetime, datetime]:
    """Get the selected date range."""
    start_date = st.date_input(
        "Start Date",
        min_value=datetime.now().date(),
        value=datetime.now().date() + timedelta(days=7)
    )
    end_date = st.date_input(
        "End Date",
        min_value=start_date,
        value=start_date + timedelta(days=7)
    )
    return start_date, end_date

def get_budget_range() -> Tuple[int, int]:
    """Get the selected budget range."""
    return st.slider(
        "Budget Range (USD)",
        min_value=500,
        max_value=10000,
        value=(1000, 3000),
        step=100
    )

def get_accommodation_type() -> str:
    """Get the selected accommodation type."""
    return st.selectbox(
        "Accommodation Type",
        ["Hotel", "Hostel", "Apartment", "Resort"]
    )

def get_travel_style() -> List[str]:
    """Get the selected travel styles."""
    return st.multiselect(
        "Travel Style",
        ["Adventure", "Relaxation", "Cultural", "Food & Wine", "Shopping", "Nature"]
    )

def get_preferences() -> Dict[str, Any]:
    """
    Get user preferences from the sidebar.
    
    Returns:
        Dictionary containing user preferences
    """
    st.header("Trip Preferences")
    
    # Get all preferences
    start_date, end_date = get_date_range()
    budget_range = get_budget_range()
    accommodation_type = get_accommodation_type()
    travel_style = get_travel_style()
    
    # Return preferences as dictionary
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "budget_range": budget_range,
        "accommodation_type": accommodation_type,
        "travel_style": travel_style
    } 