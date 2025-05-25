import streamlit as st
from typing import Dict, Any
from app.utils.api import chat_with_agent, APIError
import json
from datetime import datetime

def display_agent_status(agent_name: str, status: str):
    """Display the status of an agent's processing."""
    with st.status(f"{agent_name} 처리 중...", state=status):
        st.write(f"{agent_name}가 작업을 수행하고 있습니다.")

def display_collaboration_results(results: Dict[str, Any]):
    """Display results from multiple agents."""
    if "collaboration_results" in results:
        primary_agent = results["collaboration_results"]["primary_agent"]
        supporting_agents = results["collaboration_results"]["supporting_responses"]
        
        # Display primary agent's response
        st.write(f"**{primary_agent}의 응답:**")
        st.write(results["collaboration_results"]["primary_response"]["message"])
        
        # Display supporting agents' responses
        if supporting_agents:
            st.write("**추가 정보:**")
            for agent, response in supporting_agents.items():
                with st.expander(f"{agent}의 추가 정보"):
                    st.write(response["message"])

def display_chat_message(message: Dict[str, Any], is_user: bool = False):
    """채팅 메시지를 표시합니다."""
    if is_user:
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])
        if not is_user and "data" in message:
            display_response_data(message["data"])
            if "collaboration_results" in message["data"]:
                display_collaboration_results(message["data"])

def display_response_data(data: Dict[str, Any]):
    """Display additional data from the agent's response."""
    if "budget_estimate" in data:
        st.write("**예산 추정:**")
        budget = data["budget_estimate"]
        st.write(f"총 예산: ₩{budget['total']:,}")
        st.write("**세부 내역:**")
        for category, amount in budget["breakdown"].items():
            st.write(f"- {category}: ₩{amount:,}")
    
    if "calendar_prompt" in data:
        st.write("**캘린더 통합:**")
        st.write(data["calendar_prompt"])
        if data.get("needs_calendar_confirmation"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("예, 캘린더에 추가"):
                    st.session_state.calendar_confirmation = "yes"
            with col2:
                if st.button("아니오, 건너뛰기"):
                    st.session_state.calendar_confirmation = "no"

def display_chat_history(chat_history):
    """채팅 기록을 표시합니다."""
    for message in chat_history:
        display_chat_message(message, message["role"] == "user")

def display_preferences_form():
    """여행 선호사항 입력 폼을 표시합니다."""
    st.subheader("여행 선호사항")
    
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
    if st.button("선호사항 저장"):
        return {
            "budget": budget,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "accommodation_type": accommodation_type,
            "travel_style": travel_style,
            "preferences": preferences
        }
    return None

def format_user_preferences(preferences):
    """사용자 선호사항을 포맷팅합니다."""
    formatted = []
    
    if preferences.get("budget"):
        formatted.append(f"예산: {preferences['budget']}만원")
    
    if preferences.get("start_date") and preferences.get("end_date"):
        formatted.append(f"여행 기간: {preferences['start_date']} ~ {preferences['end_date']}")
    
    if preferences.get("accommodation_type"):
        formatted.append(f"숙소 유형: {preferences['accommodation_type']}")
    
    if preferences.get("travel_style"):
        formatted.append(f"여행 스타일: {preferences['travel_style']}")
    
    if preferences.get("preferences"):
        formatted.append(f"선호사항: {preferences['preferences']}")
    
    return "\n".join(formatted)

def initialize_chat():
    """채팅을 초기화합니다."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "user_preferences" not in st.session_state:
        st.session_state.user_preferences = {}

def update_user_preferences(preferences):
    """사용자 선호사항을 업데이트합니다."""
    st.session_state.user_preferences = preferences
    
    # 선호사항이 변경되면 새로운 메시지 추가
    if preferences:
        formatted_prefs = format_user_preferences(preferences)
        if formatted_prefs:
            st.session_state.messages.append({
                "role": "user",
                "content": f"다음과 같은 여행 계획을 세워주세요:\n{formatted_prefs}"
            })

def display_chat_interface():
    """채팅 인터페이스를 표시합니다."""
    # 채팅 기록 표시
    for message in st.session_state.messages:
        display_chat_message(message, message["role"] == "user")
    
    # 사용자 입력
    if prompt := st.chat_input("메시지를 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_chat_message({"content": prompt}, True)
        
        try:
            # Create a placeholder for streaming response
            response_placeholder = st.empty()
            full_response = ""
            # Spinner while waiting for response
            with st.spinner("AI가 답변을 생성 중입니다..."):
                # Send message to agent with streaming
                for chunk in chat_with_agent({
                    "message": prompt,
                    "history": st.session_state.messages,
                    "preferences": st.session_state.user_preferences,
                    "stream": True
                }):
                    if chunk.get("type") == "message":
                        full_response += chunk["content"]
                        response_placeholder.markdown(full_response + "▌")
                    elif chunk.get("type") == "collaboration":
                        display_agent_status(chunk["agent"], "running")
                    elif chunk.get("type") == "complete":
                        for agent in chunk.get("agents", []):
                            display_agent_status(agent, "complete")
            # Add agent response to history
            agent_message = {
                "role": "assistant",
                "content": full_response,
                "data": chunk.get("data", {})
            }
            st.session_state.messages.append(agent_message)
            response_placeholder.markdown(full_response)
            
        except APIError as e:
            st.error(f"Error: {str(e)}") 