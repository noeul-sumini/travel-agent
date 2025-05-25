from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from app.core.config import settings

class AgentResponse(BaseModel):
    """Base response model for all agents"""
    success: bool
    message: str
    data: Dict[str, Any] = {}

class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system."""
    
    def __init__(self, name: str, role: str, tools: List[Any] = None):
        self.name = name
        self.role = role
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7
        )
        self.tools = tools or []
        self.tool_executor = ToolExecutor(self.tools)
        self.graph = self._build_graph()
        self.other_agents: Dict[str, 'BaseAgent'] = {}
        self.capabilities: List[str] = []  # Initialize capabilities
        self.collaboration_state = {}
    
    def _build_graph(self) -> StateGraph:
        """Build the agent workflow graph."""
        workflow = StateGraph(StateType=Dict[str, Any])
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tools_node)
        workflow.add_node("collaboration", self._collaboration_node)
        
        # Add edges
        workflow.add_edge("agent", "tools")
        workflow.add_edge("tools", "agent")
        workflow.add_edge("agent", "collaboration")
        workflow.add_edge("collaboration", "agent")
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Set conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "collaborate": "collaboration",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and decide next action."""
        messages = state["messages"]
        
        # Add system message if not present
        if not any(msg.type == "system" for msg in messages):
            messages.insert(0, SystemMessage(content=f"""You are {self.name}, {self.role}.
            You can collaborate with other agents when needed.
            Always provide responses in Korean."""))
        
        # Get agent response
        response = self.llm.invoke(messages)
        state["messages"].append(response)
        
        # Extract tool calls if any
        if hasattr(response, "tool_calls") and response.tool_calls:
            state["tool_calls"] = response.tool_calls
            state["next_action"] = "tools"
        else:
            state["tool_calls"] = None
            state["next_action"] = "end"
        
        # Check if collaboration is needed
        if self._needs_collaboration(response.content):
            state["next_action"] = "collaborate"
            state["collaboration_request"] = self._extract_collaboration_request(response.content)
        
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
    
    async def _collaboration_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle collaboration with other agents."""
        if not state.get("collaboration_request"):
            return state
        
        request = state["collaboration_request"]
        target_agent = self.other_agents.get(request["agent"])
        
        if target_agent:
            # Forward request to target agent
            response = await target_agent.process({
                "messages": [HumanMessage(content=request["message"])],
                "context": state.get("context", {})
            })
            
            # Add collaboration response to messages
            state["messages"].append(
                AIMessage(content=f"Response from {target_agent.name}: {response['message']}")
            )
        
        return state
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """Determine the next action in the workflow."""
        return state.get("next_action", "end")
    
    def _needs_collaboration(self, content: str) -> bool:
        """Determine if the response indicates need for collaboration."""
        # This is a simple implementation. You might want to use LLM to make this decision
        collaboration_keywords = ["need help from", "collaborate with", "ask", "consult"]
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
        return None
    
    def add_agent(self, agent: 'BaseAgent') -> None:
        """Add another agent for potential collaboration."""
        self.other_agents[agent.name] = agent
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return response."""
        # Prepare state
        state = {
            "messages": context.get("messages", []),
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

    def can_handle(self, intent: str) -> bool:
        """Check if this agent can handle the given intent"""
        return intent in self.capabilities
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this agent has"""
        return self.capabilities

    def _process_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    async def _collaborate_with_agent(self, agent_name: str, message: str, context: dict) -> dict:
        try:
            # Get the agent instance
            agent = self.collaboration_state.get(agent_name)
            if not agent:
                return {
                    "status": "error",
                    "error": f"Agent {agent_name} not found"
                }
            
            # Process the message
            response = await agent.process_message(message)
            
            return {
                "status": "success",
                "data": response
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _coordinate_collaboration(self, message: str, context: dict) -> dict:
        try:
            # Extract collaboration request
            request = self._extract_collaboration_request(message)
            if not request:
                return {
                    "status": "error",
                    "error": "Could not determine which agent to collaborate with"
                }
            
            # Get initial response from the primary agent
            primary_response = await self._collaborate_with_agent(
                request["agent"],
                request["message"],
                context
            )
            
            if primary_response["status"] == "error":
                return primary_response
            
            # Process the response
            final_response = self._process_collaboration_response(
                primary_response["data"],
                context
            )
            
            return {
                "status": "success",
                "data": final_response
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _process_collaboration_response(self, response: dict, context: dict) -> dict:
        return response

    async def process_message(self, message: str) -> dict:
        try:
            # Prepare the state
            state = {
                "messages": [HumanMessage(content=message)],
                "context": {},
                "next_action": "process"
            }
            
            # Run the graph
            result = await self.graph.ainvoke(state)
            
            return {
                "status": "success",
                "data": result.get("response", "")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 