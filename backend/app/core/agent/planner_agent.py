from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from app.core.config import settings
from app.core.agent.base_agent import BaseAgent
from app.tools.budget import BudgetTool
from app.tools.weather import WeatherTool
from app.tools.maps import MapsTool
from app.tools.flights import FlightsTool

class PlannerAgent(BaseAgent):
    """Travel planning agent that can collaborate with other agents."""
    
    def __init__(self):
        super().__init__(
            name="PlannerAgent",
            role="travel planning expert",
            tools=[
                BudgetTool(),
                WeatherTool(),
                MapsTool(),
                FlightsTool()
            ]
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
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("tools", self._tools_node)
        
        # Add edges
        workflow.add_edge("planner", "tools")
        workflow.add_edge("tools", "planner")
        
        # Set entry point
        workflow.set_entry_point("planner")
        
        # Set conditional edges
        workflow.add_conditional_edges(
            "planner",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _planner_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and decide next action."""
        messages = state["messages"]
        
        # Add system message for planning
        if not any(msg.type == "system" for msg in messages):
            messages.insert(0, HumanMessage(content="""You are a travel planning expert. Your role is to:
            1. Understand user's travel preferences and requirements
            2. Create detailed travel plans
            3. Search for places and activities
            4. Estimate budgets
            5. Check weather conditions
            6. Find transportation options
            
            Always provide responses in Korean and consider local context."""))
        
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
        """Process a planning request."""
        # Prepare state
        state = {
            "messages": [
                HumanMessage(content=f"""Create a travel plan with these details:
                Destination: {context.get('destination')}
                Start Date: {context.get('start_date')}
                End Date: {context.get('end_date')}
                Preferences: {context.get('preferences', {})}""")
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
            "check calendar", "schedule", "add to calendar",
            "check weather", "weather forecast",
            "find flights", "search flights",
            "calculate budget", "estimate costs"
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
            elif "check calendar" in line.lower() or "schedule" in line.lower():
                return {
                    "agent": "CalendarAgent",
                    "message": content
                }
            elif "check weather" in line.lower():
                return {
                    "agent": "WeatherAgent",
                    "message": content
                }
            elif "find flights" in line.lower() or "search flights" in line.lower():
                return {
                    "agent": "FlightAgent",
                    "message": content
                }
            elif "calculate budget" in line.lower() or "estimate costs" in line.lower():
                return {
                    "agent": "BudgetAgent",
                    "message": content
                }
        return None 