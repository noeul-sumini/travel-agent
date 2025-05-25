from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from app.core.logging import logger

class BaseTravelTool(BaseTool):
    """Base class for all travel-related tools."""
    
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info(f"Initialized tool: {self.name}")

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """Async implementation of the tool."""
        raise NotImplementedError("Async execution not implemented")

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Sync implementation of the tool."""
        raise NotImplementedError("Sync execution not implemented")

    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters."""
        return True

    def format_output(self, result: Any) -> Dict[str, Any]:
        """Format the tool's output."""
        return {
            "status": "success",
            "data": result,
            "tool": self.name
        }

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors in tool execution."""
        logger.error(f"Error in {self.name}: {str(error)}")
        return {
            "status": "error",
            "error": str(error),
            "tool": self.name
        } 