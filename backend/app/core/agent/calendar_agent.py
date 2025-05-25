from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from app.core.config import settings
from app.core.agent.base_agent import BaseAgent
from app.tools.calendar import CalendarTool

class CalendarAgent(BaseAgent):
    """Calendar management agent that can collaborate with other agents."""
    
    def __init__(self):
        super().__init__(
            name="CalendarAgent",
            role="calendar management expert",
            tools=[CalendarTool()]
        )
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_NAME,
            temperature=0.7
        )
        self.tool_executor = ToolExecutor(self.tools)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the agent workflow graph."""
        workflow = StateGraph(StateType=Dict[str, Any])
        
        # Add nodes
        workflow.add_node("calendar", self._calendar_node)
        workflow.add_node("tools", self._tools_node)
        
        # Add edges
        workflow.add_edge("calendar", "tools")
        workflow.add_edge("tools", "calendar")
        
        # Set entry point
        workflow.set_entry_point("calendar")
        
        # Set conditional edges
        workflow.add_conditional_edges(
            "calendar",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _calendar_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and decide next action."""
        messages = state["messages"]
        
        # Add system message for calendar management
        if not any(msg.type == "system" for msg in messages):
            messages.insert(0, HumanMessage(content="""You are a calendar management expert. Your role is to:
            1. Create calendar events from travel plans
            2. Manage event details and reminders
            3. Handle event updates and cancellations
            4. Coordinate with other calendar systems
            
            Always provide responses in Korean and consider local time zones."""))
        
        # Get agent response
        response = self.llm.invoke(messages)
        state["messages"].append(response)
        
        # Extract tool calls if any
        if hasattr(response, "tool_calls") and response.tool_calls:
            state["tool_calls"] = response.tool_calls
        else:
            state["tool_calls"] = None
        
        return state
    
    def _tools_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tools based on agent's decision."""
        if not state.get("tool_calls"):
            return state
        
        # Execute tools
        tool_results = self.tool_executor.batch(
            state["tool_calls"],
            {"messages": state["messages"]}
        )
        
        # Add tool results to messages
        for result in tool_results:
            state["messages"].append(
                AIMessage(content=str(result))
            )
        
        return state
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """Determine if the agent should continue or end."""
        if state.get("tool_calls"):
            return "continue"
        return "end"
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a calendar request."""
        # Prepare state
        state = {
            "messages": [
                HumanMessage(content=f"""Handle this calendar request:
                Plan: {context.get('plan')}
                Action: {context.get('intent')}
                Additional Info: {context.get('additional_info', {})}""")
            ],
            "context": context
        }
        
        # Run the graph
        final_state = await self.graph.arun(state)
        
        # Get the last AI message
        response = final_state["messages"][-1]
        
        return {
            "message": response.content,
            "data": final_state.get("data", {})
        }
    
    def _needs_collaboration(self, content: str) -> bool:
        """Determine if the response indicates need for collaboration."""
        collaboration_keywords = [
            "need help from", "collaborate with", "ask", "consult",
            "check weather", "weather forecast",
            "find location", "get directions",
            "check availability", "find time slot"
        ]
        return any(keyword in content.lower() for keyword in collaboration_keywords)
    
    def _extract_collaboration_request(self, content: str) -> Dict[str, Any]:
        """Extract collaboration request details from the response."""
        # This is a simple implementation. You might want to use LLM to parse this
        lines = content.split("\n")
        for line in lines:
            if "need help from" in line.lower():
                agent_name = line.split("from")[-1].strip()
                return {
                    "agent": agent_name,
                    "message": content
                }
            elif "check weather" in line.lower():
                return {
                    "agent": "WeatherAgent",
                    "message": content
                }
            elif "find location" in line.lower() or "get directions" in line.lower():
                return {
                    "agent": "MapsAgent",
                    "message": content
                }
            elif "check availability" in line.lower() or "find time slot" in line.lower():
                return {
                    "agent": "PlannerAgent",
                    "message": content
                }
        return None

    async def create_event(self, event_data: dict) -> dict:
        try:
            result = await self.calendar_tool.create_event(event_data)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_event(self, event_id: str) -> dict:
        try:
            result = await self.calendar_tool.get_event(event_id)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def update_event(self, event_id: str, event_data: dict) -> dict:
        try:
            result = await self.calendar_tool.update_event(event_id, event_data)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def delete_event(self, event_id: str) -> dict:
        try:
            result = await self.calendar_tool.delete_event(event_id)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def create_travel_events(self, travel_plan: dict) -> dict:
        try:
            events = []
            
            # Create event for each activity
            for activity in travel_plan.get("activities", []):
                event_data = {
                    "title": activity["name"],
                    "description": activity.get("description", ""),
                    "start": activity["start_time"],
                    "end": activity["end_time"],
                    "location": activity.get("location", "")
                }
                event = await self.calendar_tool.create_event(event_data)
                events.append(event)
            
            # Create event for each accommodation
            for accommodation in travel_plan.get("accommodations", []):
                event_data = {
                    "title": f"Stay at {accommodation['name']}",
                    "description": f"Accommodation at {accommodation['name']}",
                    "start": accommodation["check_in"],
                    "end": accommodation["check_out"],
                    "location": accommodation.get("location", "")
                }
                event = await self.calendar_tool.create_event(event_data)
                events.append(event)
            
            # Create event for each transportation
            for transport in travel_plan.get("transportation", []):
                event_data = {
                    "title": f"{transport['type'].title()} from {transport['from']} to {transport['to']}",
                    "description": f"Transportation details: {transport.get('details', '')}",
                    "start": transport["departure"],
                    "end": transport["arrival"],
                    "location": f"{transport['from']} to {transport['to']}"
                }
                event = await self.calendar_tool.create_event(event_data)
                events.append(event)
            
            return {
                "status": "success",
                "data": events
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _process_node(self, state: AgentState) -> AgentState:
        return state

    async def process_calendar_request(self, request: str) -> dict:
        try:
            # Extract event details from request
            event_data = self._extract_event_details(request)
            
            if not event_data:
                return {
                    "status": "error",
                    "error": "Could not extract event details from request"
                }
            
            # Create the event
            return await self.create_event(event_data)
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _extract_event_details(self, request: str) -> Optional[dict]:
        # In a real implementation, this would use NLP to extract event details
        # For now, return None to indicate extraction failure
        return None 