from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.api.schemas import ChatRequest
from app.core.agent.travel_agent import TravelAgent
import uuid
import json
import asyncio
from typing import AsyncGenerator

router = APIRouter()

# Initialize travel agent
travel_agent = TravelAgent()

async def generate_stream(
    session_id: str,
    message: str,
    context: dict
) -> AsyncGenerator[str, None]:
    """
    Generate a stream of responses from the travel agent.
    
    Args:
        session_id: Session ID for conversation tracking
        message: User's message
        context: Context information
    
    Yields:
        JSON strings containing partial responses
    """
    try:
        # Process message with streaming
        async for chunk in travel_agent.process_message_stream(
            session_id=session_id,
            message=message,
            context=context
        ):
            # Yield each chunk as a JSON string
            yield f"data: {json.dumps(chunk)}\n\n"
            
    except Exception as e:
        # Send error as a stream chunk
        error_chunk = {
            "type": "error",
            "content": str(e)
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Process a chat message and return a stream of the agent's responses.
    
    Args:
        request: ChatRequest containing:
            - message: User's message
            - session_id: Optional session ID for conversation tracking
            - context: Optional context information
    
    Returns:
        StreamingResponse containing the agent's responses
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Return streaming response
        return StreamingResponse(
            generate_stream(
                session_id=session_id,
                message=request.message,
                context=request.context or {}
            ),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 