import requests
from typing import Dict, Any, Generator
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(f".env.{os.getenv('ENV', 'dev')}")

# API Configuration
API_BASE_URL = f"http://{os.getenv('BACKEND_HOST', 'localhost')}:{os.getenv('BACKEND_PORT', '8000')}/api"

class APIError(Exception):
    """Custom exception for API errors"""
    pass

def chat_with_agent(context: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    Send a message to the travel agent and get a streaming response.
    
    Args:
        context: Dictionary containing conversation context including:
            - message: User's message
            - history: Previous conversation history
            - preferences: User preferences (if any)
            - current_plan: Current travel plan (if any)
            - stream: Whether to stream the response
    
    Yields:
        Dictionary containing chunks of the agent's response
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "message": context.get("message", ""),
                "session_id": context.get("session_id"),
                "context": {
                    "history": context.get("history", []),
                    "preferences": context.get("preferences", {}),
                    "current_plan": context.get("current_plan")
                }
            },
            headers={"Content-Type": "application/json"},
            stream=context.get("stream", True)
        )
        response.raise_for_status()
        
        if context.get("stream", True):
            for line in response.iter_lines():
                if not line:
                    continue
                
                try:
                    # Decode and parse the line
                    decoded_line = line.decode('utf-8')
                    if not decoded_line.startswith('data: '):
                        continue
                    
                    chunk = json.loads(decoded_line[6:])  # Remove 'data: ' prefix
                    yield chunk
                    
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    yield {
                        "type": "error",
                        "content": f"Error processing response: {str(e)}"
                    }
        else:
            yield response.json()
            
    except requests.exceptions.RequestException as e:
        yield {
            "type": "error",
            "content": f"Failed to communicate with travel agent: {str(e)}"
        }

def create_travel_plan(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new travel plan."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/travel-plan",
            json={
                "preferences": preferences
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Failed to create travel plan: {str(e)}")

def process_calendar_confirmation(plan_id: str, confirmation: str) -> Dict[str, Any]:
    """Process user's confirmation for calendar integration."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/calendar/confirm",
            json={
                "plan_id": plan_id,
                "confirmation": confirmation
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Failed to process calendar confirmation: {str(e)}")

def add_to_calendar(plan_id: str) -> Dict[str, Any]:
    """Add a travel plan to calendar."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/calendar/add",
            json={"plan_id": plan_id}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Failed to add to calendar: {str(e)}")

def share_travel_plan(plan_id: str, format: str = "html") -> Dict[str, Any]:
    """Share a travel plan."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/travel-plan/share",
            json={
                "plan_id": plan_id,
                "format": format
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Failed to share travel plan: {str(e)}") 