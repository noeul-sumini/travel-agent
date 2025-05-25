import streamlit as st
from datetime import datetime
from typing import Dict, Any
from functools import lru_cache
import asyncio

@lru_cache(maxsize=128)
def format_date(date_str: str) -> str:
    """Format ISO date string to readable format."""
    return datetime.fromisoformat(date_str).strftime("%Y-%m-%d")

@lru_cache(maxsize=128)
def format_time(time_str: str) -> str:
    """Format ISO time string to readable format."""
    return datetime.fromisoformat(time_str).strftime("%H:%M")

@lru_cache(maxsize=128)
def format_currency(amount: float, currency: str) -> str:
    """Format currency amount."""
    return f"{currency} {amount:,.2f}"

async def load_activity_details(activity_id: str) -> Dict[str, Any]:
    """Lazy load activity details."""
    # Simulate API call
    await asyncio.sleep(0.1)
    return {
        "description": "Detailed description...",
        "reviews": []
    }

async def load_accommodation_details(accommodation_id: str) -> Dict[str, Any]:
    """Lazy load accommodation details."""
    # Simulate API call
    await asyncio.sleep(0.1)
    return {
        "amenities": ["wifi", "pool"],
        "reviews": []
    }

def display_activities(activities: list) -> None:
    """Display activities section with lazy loading."""
    st.subheader("Activities")
    for activity in activities:
        with st.expander(f"📅 {activity['name']}", expanded=False):
            # Basic info immediately displayed
            st.write(f"**Location:** {activity['location']}")
            st.write(f"**Time:** {format_time(activity['start_time'])} - "
                    f"{format_time(activity['end_time'])}")
            
            # Load detailed info when expanded
            if st.session_state.get(f"expanded_{activity['name']}", False):
                with st.spinner("Loading details..."):
                    details = asyncio.run(load_activity_details(activity['id']))
                    st.write(f"**Description:** {details['description']}")

def display_accommodations(accommodations: list) -> None:
    """Display accommodations section with lazy loading."""
    st.subheader("Accommodations")
    for accommodation in accommodations:
        with st.expander(f"🏨 {accommodation['name']}", expanded=False):
            # Basic info immediately displayed
            st.write(f"**Location:** {accommodation['location']}")
            st.write(f"**Check-in:** {format_date(accommodation['check_in'])}")
            st.write(f"**Check-out:** {format_date(accommodation['check_out'])}")
            
            # Load detailed info when expanded
            if st.session_state.get(f"expanded_{accommodation['name']}", False):
                with st.spinner("Loading details..."):
                    details = asyncio.run(load_accommodation_details(accommodation['id']))
                    st.write("**Amenities:**")
                    for amenity in details['amenities']:
                        st.write(f"- {amenity}")

def display_transportation(transportation: list) -> None:
    """Display transportation section."""
    st.subheader("Transportation")
    for transport in transportation:
        with st.expander(f"✈️ {transport['type'].title()} from {transport['from']} to {transport['to']}", expanded=False):
            st.write(f"**Departure:** {format_date(transport['departure'])} {format_time(transport['departure'])}")
            st.write(f"**Arrival:** {format_date(transport['arrival'])} {format_time(transport['arrival'])}")

def display_budget(budget: Dict[str, Any]) -> None:
    """Display budget section."""
    st.subheader("Budget")
    st.write(f"**Total Budget:** {format_currency(budget['total'], budget['currency'])}")
    
    # Create a pie chart for budget breakdown
    breakdown = budget['breakdown']
    st.write("**Budget Breakdown:**")
    for category, amount in breakdown.items():
        st.write(f"- {category.title()}: {format_currency(amount, budget['currency'])}")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def display_travel_plan(plan: Dict[str, Any]) -> None:
    """Display the complete travel plan."""
    st.header(f"Travel Plan for {plan['destination']}")
    
    # Display dates
    st.subheader(f"Dates: {format_date(plan['start_date'])} to {format_date(plan['end_date'])}")
    
    # Display each section
    display_activities(plan['activities'])
    display_accommodations(plan['accommodations'])
    display_transportation(plan['transportation'])
    display_budget(plan['budget'])
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 Add to Calendar"):
            try:
                from app.utils.api import add_to_calendar
                add_to_calendar(plan['id'])
                st.success("Added to calendar!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("📤 Share Plan"):
            try:
                from app.utils.api import share_travel_plan
                share_travel_plan(plan['id'])
                st.success("Plan shared!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def display_travel_plan_form():
    """여행 계획 입력 폼을 표시합니다."""
    st.subheader("여행 계획 입력")
    
    # 예산 입력 (만원 단위)
    budget = st.number_input(
        "예산 (만원)",
        min_value=0,
        max_value=10000,
        value=1000,
        step=100,
        help="예산을 만원 단위로 입력해주세요"
    )
    
    # 여행 기간
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("출발일")
    with col2:
        end_date = st.date_input("도착일")
    
    # 숙소 유형
    accommodation_type = st.selectbox(
        "숙소 유형",
        ["호텔", "에어비앤비", "호스텔", "게스트하우스", "리조트"]
    )
    
    # 여행 스타일
    travel_style = st.selectbox(
        "여행 스타일",
        ["관광", "휴양", "미식", "쇼핑", "자연", "기타"]
    )
    
    # 추가 선호사항
    preferences = st.text_area("추가 선호사항", help="특별히 원하시는 활동이나 장소가 있다면 입력해주세요")
    
    # 제출 버튼
    if st.button("여행 계획 생성"):
        return {
            "budget": budget,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "accommodation_type": accommodation_type,
            "travel_style": travel_style,
            "preferences": preferences
        }
    return None 