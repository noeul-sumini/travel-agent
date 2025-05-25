import streamlit as st
from app.components.Chat import chat_interface

def format_currency(amount: int) -> str:
    """Format currency amount in KRW."""
    return f"₩{amount:,}"

def main():
    st.set_page_config(
        page_title="Travel Agent",
        page_icon="✈️",
        layout="wide"
    )
    
    st.title("Travel Agent")
    
    # Initialize session state
    if "context" not in st.session_state:
        st.session_state.context = {
            "history": [],
            "current_plan": None
        }
    
    # Main chat interface
    chat_interface(st.session_state.context)
    
    # Display current plan if available
    if st.session_state.context.get("current_plan"):
        st.subheader("Current Travel Plan")
        plan = st.session_state.context["current_plan"]
        
        # Display plan details
        st.write(f"**Destination:** {plan['destination']}")
        st.write(f"**Dates:** {plan['start_date']} to {plan['end_date']}")
        
        # Display activities
        if "activities" in plan:
            st.write("**Activities:**")
            for activity in plan["activities"]:
                st.write(f"- {activity['name']} at {activity['location']}")
        
        # Display accommodations
        if "accommodations" in plan:
            st.write("**Accommodations:**")
            for accommodation in plan["accommodations"]:
                st.write(f"- {accommodation['name']} ({accommodation['type']})")
        
        # Display budget
        if "budget" in plan:
            st.write("**Budget:**")
            st.write(f"Total: {format_currency(plan['budget']['total'])}")
            for category, amount in plan['budget']['breakdown'].items():
                st.write(f"- {category}: {format_currency(amount)}")

if __name__ == "__main__":
    main() 