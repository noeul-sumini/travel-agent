from typing import Dict, List, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from app.core.config import settings
from app.core.logging import logger

class BaseAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL_NAME,
            temperature=0.7,
            streaming=True
        )
        self.tools = []
        self.tool_executor = None
        self.graph = None

    def add_tool(self, tool: Any):
        """Add a tool to the agent."""
        self.tools.append(tool)
        self.tool_executor = ToolExecutor(self.tools)

    def create_graph(self):
        """Create the agent's workflow graph."""
        workflow = StateGraph(StateType=Dict)

        # Define nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tools_node)

        # Define edges
        workflow.add_edge("agent", "tools")
        workflow.add_edge("tools", "agent")
        workflow.add_edge("agent", END)

        # Set entry point
        workflow.set_entry_point("agent")

        # Compile graph
        self.graph = workflow.compile()

    async def _agent_node(self, state: Dict) -> Dict:
        """Process the current state and decide next action."""
        messages = state.get("messages", [])
        
        # Get response from LLM
        response = await self.llm.ainvoke(messages)
        
        # Update state with response
        state["messages"].append(response)
        
        # Check if we should use tools
        if "tool_calls" in response.additional_kwargs:
            return "tools"
        
        return END

    async def _tools_node(self, state: Dict) -> Dict:
        """Execute tools and update state."""
        messages = state.get("messages", [])
        last_message = messages[-1]
        
        # Execute tools
        tool_results = await self.tool_executor.ainvoke(
            last_message.additional_kwargs["tool_calls"]
        )
        
        # Add tool results to messages
        state["messages"].append(
            AIMessage(content=str(tool_results))
        )
        
        return "agent"

    async def run(self, messages: List[BaseMessage]) -> Dict:
        """Run the agent with given messages."""
        if not self.graph:
            self.create_graph()
        
        # Initialize state
        state = {"messages": messages}
        
        # Run the graph
        result = await self.graph.arun(state)
        
        return result

    async def stream(self, messages: List[BaseMessage]):
        """Stream the agent's responses."""
        if not self.graph:
            self.create_graph()
        
        # Initialize state
        state = {"messages": messages}
        
        # Stream the graph execution
        async for event in self.graph.astream(state):
            if "messages" in event and event["messages"]:
                last_message = event["messages"][-1]
                if isinstance(last_message, AIMessage):
                    yield last_message.content 