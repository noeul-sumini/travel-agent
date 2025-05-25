import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from app.components.TravelPlan import display_travel_plan_form
from app.components.Chat import initialize_chat, update_user_preferences, display_chat_interface

st.set_page_config(
    page_title="여행 계획 도우미",
    page_icon="✈️",
    layout="wide"
)

# Load environment variables
load_dotenv(f".env.{os.getenv('ENV', 'dev')}")

# Constants
BACKEND_URL = f"http://{os.getenv('BACKEND_HOST', 'localhost')}:{os.getenv('BACKEND_PORT', '8000')}"

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 1rem;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.assistant {
        background-color: #475063;
    }
    .chat-message .avatar {
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "travel_plan" not in st.session_state:
    st.session_state.travel_plan = None

def send_message(message, stream=True):
    """Send message to backend and handle streaming response."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={
                "messages": [{"role": "user", "content": message}],
                "stream": stream
            },
            stream=stream
        )
        response.raise_for_status()
        
        if stream:
            return response.iter_lines()
        else:
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with server: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def create_travel_plan(destination, start_date, end_date, preferences=None):
    """Create a travel plan using the backend API."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/travel-plan",
            json={
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "preferences": preferences
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error creating travel plan: {str(e)}")
        return None

def sidebar_preferences():
    st.sidebar.title("여행 선호도 입력")
    budget = st.sidebar.number_input(
        "예산 (만원)", min_value=0, max_value=10000, value=1000, step=100, help="예산을 만원 단위로 입력해주세요"
    )
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("출발일")
    with col2:
        end_date = st.date_input("도착일")
    accommodation_type = st.sidebar.selectbox(
        "숙소 유형", ["호텔", "에어비앤비", "호스텔", "게스트하우스", "리조트"]
    )
    travel_style = st.sidebar.selectbox(
        "여행 스타일", ["관광", "휴양", "미식", "쇼핑", "자연", "기타"]
    )
    preferences = st.sidebar.text_area("추가 선호사항", help="특별히 원하시는 활동이나 장소가 있다면 입력해주세요")
    st.session_state.user_preferences = {
        "budget": budget,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "accommodation_type": accommodation_type,
        "travel_style": travel_style,
        "preferences": preferences
    }

def main():
    st.title("여행 계획 도우미")
    sidebar_preferences()
    initialize_chat()
    display_chat_interface()

if __name__ == "__main__":
    main() 