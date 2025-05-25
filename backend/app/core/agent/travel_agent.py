from typing import Dict, Any, List, Tuple, Annotated, Optional
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from app.core.config import settings
from app.core.chat_history import ChatHistoryManager
from app.tools.budget import BudgetTool
from app.tools.weather import WeatherTool
from app.tools.calendar import CalendarTool
from app.tools.maps import MapsTool
from app.tools.flights import FlightsTool
from app.core.agent.base_agent import BaseAgent
from app.core.agent.planner_agent import PlannerAgent
from app.core.agent.calendar_agent import CalendarAgent
from app.core.agent.weather_agent import WeatherAgent
from app.core.agent.maps_agent import MapsAgent
from app.core.agent.flight_agent import FlightAgent
from app.core.agent.budget_agent import BudgetAgent
from typing import AsyncGenerator

class TravelAgent(BaseAgent):
    """Main travel agent that coordinates with other specialized agents."""
    
    def __init__(self):
        super().__init__(
            name="TravelAgent",
            role="travel coordination expert"
        )
        
        # Initialize specialized agents
        self.planner = PlannerAgent()
        self.calendar = CalendarAgent()
        self.weather = WeatherAgent()
        self.maps = MapsAgent()
        self.flights = FlightAgent()
        self.budget = BudgetAgent()
        
        # Set up agent network
        self.graph = self._setup_agent_network()
        
        # Initialize collaboration state
        self.collaboration_state = {}
    
    def _setup_agent_network(self):
        """Set up the network of collaborating agents."""
        # Add all agents to each other's network
        agents = [
            self.planner,
            self.calendar,
            self.weather,
            self.maps,
            self.flights,
            self.budget
        ]
        
        for agent in agents:
            for other in agents:
                if agent != other:
                    agent.add_agent(other)
        
        # Create the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("start", self._start_node)
        workflow.add_node("process", self._process_node)
        workflow.add_node("calendar", self._calendar_node)
        workflow.add_node("end", self._end_node)
        
        # Add edges
        workflow.add_edge("start", "process")
        workflow.add_conditional_edges(
            "process",
            self._needs_collaboration,
            {
                True: "calendar",
                False: "end"
            }
        )
        workflow.add_edge("calendar", "end")
        
        # Set entry point
        workflow.set_entry_point("start")
        
        return workflow.compile()
    
    def _needs_collaboration(self, state: AgentState) -> bool:
        """Determine if the response indicates need for collaboration."""
        # The main travel agent always delegates to specialized agents
        return True
    
    def _extract_collaboration_request(self, content: str) -> Optional[str]:
        """Extract collaboration request details from the response."""
        keywords = {
            "calendar": ["calendar", "schedule", "event"],
            "maps": ["map", "location", "place", "restaurant"],
            "weather": ["weather", "forecast", "temperature"],
            "flights": ["flight", "airplane", "airport"],
            "budget": ["budget", "cost", "price", "expense"]
        }
        
        content_lower = content.lower()
        for agent, words in keywords.items():
            if any(word in content_lower for word in words):
                return agent
        return None
    
    async def _collaborate_with_agent(
        self,
        agent_name: str,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collaborate with a specific agent."""
        agent = getattr(self, agent_name.lower().replace("agent", ""))
        return await agent.process({
            "messages": [HumanMessage(content=message)],
            "context": context
        })
    
    async def _coordinate_collaboration(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Coordinate collaboration between agents based on the request."""
        # Extract collaboration request
        request = self._extract_collaboration_request(content)
        agent_name = request
        
        # Get initial response from the primary agent
        primary_response = await self._collaborate_with_agent(
            agent_name,
            content,
            context
        )
        
        # Initialize collaboration results
        collaboration_results = {
            "primary_agent": agent_name,
            "primary_response": primary_response,
            "supporting_responses": {}
        }
        
        # Determine which supporting agents might be needed
        supporting_agents = self._get_supporting_agents(agent_name, content)
        
        # Get responses from supporting agents
        for supporting_agent in supporting_agents:
            supporting_response = await self._collaborate_with_agent(
                supporting_agent,
                f"Based on this information: {primary_response['message']}, provide additional insights.",
                {**context, "primary_response": primary_response}
            )
            collaboration_results["supporting_responses"][supporting_agent] = supporting_response
        
        # Integrate responses
        integrated_response = self._integrate_responses(collaboration_results)
        
        return {
            "message": integrated_response,
            "data": {
                "collaboration_results": collaboration_results,
                "context": context
            }
        }
    
    def _get_supporting_agents(self, primary_agent: str, content: str) -> List[str]:
        """Determine which supporting agents might be needed."""
        supporting_agents = []
        
        # Always include budget agent for cost-related insights
        if primary_agent != "BudgetAgent":
            supporting_agents.append("BudgetAgent")
        
        # Add weather agent for outdoor activities
        if any(word in content.lower() for word in ["outdoor", "weather", "forecast", "temperature"]):
            supporting_agents.append("WeatherAgent")
        
        # Add maps agent for location-based queries
        if any(word in content.lower() for word in ["location", "directions", "map", "nearby"]):
            supporting_agents.append("MapsAgent")
        
        # Add calendar agent for scheduling
        if any(word in content.lower() for word in ["schedule", "time", "when", "calendar"]):
            supporting_agents.append("CalendarAgent")
        
        return supporting_agents
    
    def _integrate_responses(self, collaboration_results: Dict[str, Any]) -> str:
        """Integrate responses from multiple agents into a coherent response."""
        primary_response = collaboration_results["primary_response"]["message"]
        supporting_responses = collaboration_results["supporting_responses"]
        
        # Start with the primary response
        integrated = primary_response
        
        # Add supporting information
        for agent, response in supporting_responses.items():
            if response["message"] and response["message"] not in integrated:
                integrated += f"\n\n추가 정보 ({agent}):\n{response['message']}"
        
        return integrated
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a travel request by coordinating with specialized agents."""
        # Add system message for the main travel agent
        if "messages" not in context:
            context["messages"] = []
        
        context["messages"].insert(0, HumanMessage(content="""You are the main travel agent.
        Your role is to coordinate with specialized agents to provide comprehensive travel assistance.
        Always provide responses in Korean."""))
        
        # Get the last user message
        last_message = context["messages"][-1].content
        
        # Coordinate collaboration between agents
        return await self._coordinate_collaboration(last_message, context)
    
    def _start_node(self, state: AgentState) -> AgentState:
        return state
    
    def _process_node(self, state: AgentState) -> AgentState:
        last_message = state.messages[-1]
        response = self.process_message(last_message.content)
        return state.update({"response": response})
    
    def _calendar_node(self, state: AgentState) -> AgentState:
        return state
    
    def _end_node(self, state: AgentState) -> AgentState:
        return state
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a user message and return agent response."""
        # Get chat history
        history = self.history_manager.get_history(session_id)
        
        # Prepare state
        state = {
            "messages": [
                *[HumanMessage(content=msg["content"]) if msg["role"] == "user"
                  else AIMessage(content=msg["content"])
                  for msg in history],
                HumanMessage(content=message)
            ],
            "context": context
        }
        
        # Run the graph
        final_state = await self.graph.arun(state)
        
        # Get the last AI message
        response = final_state["messages"][-1]
        
        # Update history
        self.history_manager.add_message(
            session_id,
            {"role": "user", "content": message}
        )
        self.history_manager.add_message(
            session_id,
            {"role": "assistant", "content": response.content}
        )
        
        # Update context if needed
        if "context" in final_state:
            self.history_manager.update_context(
                session_id,
                final_state["context"]
            )
        
        return {
            "message": response.content,
            "data": final_state.get("data", {})
        }
    
    async def create_travel_plan(self, destination: str, start_date: str, end_date: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new travel plan with a structured process"""
        try:
            # 1. Get destination details using MapsAgent
            maps_agent = self.maps
            destination_info = await maps_agent.process({
                "messages": [HumanMessage(content=f"Get detailed information about {destination} including major cities and attractions")],
                "context": {"intent": "get_destination_info"}
            })
            
            # 2. Generate travel plan using PlannerAgent
            planner_agent = self.planner
            travel_plan = await planner_agent.process({
                "messages": [HumanMessage(content=f"""Create a detailed travel plan for {destination} from {start_date} to {end_date}.
                Consider these preferences: {preferences}
                Include major cities and attractions from: {destination_info['data']}""")],
                "context": {
                    "intent": "generate_plan",
                    "destination": destination,
                    "start_date": start_date,
                    "end_date": end_date,
                    "preferences": preferences,
                    "destination_info": destination_info['data']
                }
            })
            
            # 3. Get restaurant recommendations for each location
            restaurant_recommendations = {}
            for location in travel_plan['data'].get('locations', []):
                restaurant_info = await maps_agent.process({
                    "messages": [HumanMessage(content=f"Find popular restaurants near {location['name']}")],
                    "context": {"intent": "get_restaurants"}
                })
                restaurant_recommendations[location['name']] = restaurant_info['data']
            
            # 4. Add restaurant recommendations to the plan
            travel_plan['data']['restaurants'] = restaurant_recommendations
            
            # 5. Ask user about calendar integration
            calendar_prompt = f"""여행 계획이 생성되었습니다. Google Calendar에 일정을 등록하시겠습니까?
            계획 내용:
            - 목적지: {destination}
            - 기간: {start_date} ~ {end_date}
            - 주요 도시: {', '.join(loc['name'] for loc in travel_plan['data'].get('locations', []))}
            
            Google Calendar에 등록하시려면 'yes'를, 아니면 'no'를 입력해주세요."""
            
            return {
                'success': True,
                'message': "Travel plan created successfully",
                'data': {
                    'plan': travel_plan['data'],
                    'calendar_prompt': calendar_prompt,
                    'needs_calendar_confirmation': True
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error creating travel plan: {str(e)}",
                'data': None
            }
    
    async def process_calendar_confirmation(self, plan_id: str, confirmation: str) -> Dict[str, Any]:
        """Process user's confirmation for calendar integration"""
        if confirmation.lower() == 'yes':
            return await self.add_to_calendar(plan_id)
        else:
            return {
                'success': True,
                'message': "Calendar integration skipped as per user request",
                'data': None
            }
    
    async def add_to_calendar(self, plan_id: str) -> Dict[str, Any]:
        """Add a travel plan to calendar with detailed events"""
        try:
            # Get the plan details
            plan = await self.get_travel_plan(plan_id)
            if not plan['success']:
                return plan
            
            calendar_agent = self.calendar
            
            # Create calendar events for each day
            events = []
            for day in plan['data']['plan'].get('daily_schedule', []):
                event = {
                    'summary': f"여행: {day['location']}",
                    'description': f"""일정:
                    {day['activities']}
                    
                    추천 식당:
                    {day.get('restaurants', '정보 없음')}""",
                    'start': {
                        'dateTime': day['start_time'],
                        'timeZone': 'Asia/Seoul'
                    },
                    'end': {
                        'dateTime': day['end_time'],
                        'timeZone': 'Asia/Seoul'
                    }
                }
                events.append(event)
            
            # Add events to calendar
            context = {
                'intent': 'create_events',
                'events': events
            }
            
            response = await calendar_agent.process(context)
            return {
                'success': response['success'],
                'message': "Travel plan added to calendar successfully",
                'data': response['data']
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error adding to calendar: {str(e)}",
                'data': None
            }
    
    async def get_travel_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get a specific travel plan"""
        # This would typically involve retrieving from a database
        # For now, we'll return a placeholder
        return {
            'success': True,
            'message': "Travel plan retrieved successfully",
            'data': {'plan_id': plan_id}
        }
    
    async def share_travel_plan(self, plan_id: str, format: str = "html") -> Dict[str, Any]:
        """Share a travel plan"""
        # This would typically involve generating a shareable link
        # For now, we'll return a placeholder
        return {
            'success': True,
            'message': "Travel plan shared successfully",
            'data': {'share_url': f"https://example.com/plans/{plan_id}"}
        }
    
    async def process_message_stream(
        self,
        session_id: str,
        message: str,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a user message and stream the agent's responses."""
        # Get chat history
        history = self.history_manager.get_history(session_id)
        
        # Prepare state
        state = {
            "messages": [
                *[HumanMessage(content=msg["content"]) if msg["role"] == "user"
                  else AIMessage(content=msg["content"])
                  for msg in history],
                HumanMessage(content=message)
            ],
            "context": context
        }
        
        # Update history with user message
        self.history_manager.add_message(
            session_id,
            {"role": "user", "content": message}
        )
        
        try:
            # Coordinate collaboration and stream results
            collaboration_result = await self._coordinate_collaboration(message, context)
            
            # Stream primary agent's response
            yield {
                "type": "message",
                "content": collaboration_result["message"],
                "data": collaboration_result.get("data", {})
            }
            
            # Stream supporting agents' responses
            for agent, response in collaboration_result["data"]["collaboration_results"]["supporting_responses"].items():
                yield {
                    "type": "collaboration",
                    "agent": agent,
                    "content": response["message"],
                    "data": response.get("data", {})
                }
            
            # Update history with final response
            self.history_manager.add_message(
                session_id,
                {"role": "assistant", "content": collaboration_result["message"]}
            )
            
            # Update context
            if "context" in collaboration_result["data"]:
                self.history_manager.update_context(
                    session_id,
                    collaboration_result["data"]["context"]
                )
            
            # Yield completion status
            yield {
                "type": "complete",
                "status": "finished"
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "content": str(e)
            }
            raise 