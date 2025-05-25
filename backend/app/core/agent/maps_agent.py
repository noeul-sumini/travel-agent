from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from app.core.config import settings
from app.core.agent.base_agent import BaseAgent
from app.tools.maps import MapsTool
import googlemaps
from datetime import datetime

class MapsAgent(BaseAgent):
    """Agent for handling location-based queries using Google Maps API."""
    
    def __init__(self):
        super().__init__(
            name="MapsAgent",
            role="location and place expert"
        )
        
        # Initialize Google Maps client
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        
        # Initialize tools
        self.tools = [MapsTool()]
        self.tool_executor = ToolExecutor(self.tools)
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process location-based queries."""
        try:
            intent = context.get("intent")
            messages = context.get("messages", [])
            
            if intent == "get_destination_info":
                return await self._get_destination_info(messages[0].content)
            elif intent == "get_restaurants":
                return await self._get_restaurants(messages[0].content)
            else:
                return await self._process_general_query(messages[0].content)
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing location query: {str(e)}",
                "data": None
            }
    
    async def _get_destination_info(self, query: str) -> Dict[str, Any]:
        """Get detailed information about a destination."""
        try:
            # Extract destination name from query
            destination = query.split("about")[-1].strip()
            
            # Search for the destination
            places_result = self.gmaps.places(
                query=destination,
                type="locality"
            )
            
            if not places_result.get("results"):
                return {
                    "success": False,
                    "message": f"Could not find information about {destination}",
                    "data": None
                }
            
            # Get the first result
            place = places_result["results"][0]
            place_id = place["place_id"]
            
            # Get detailed information
            place_details = self.gmaps.place(
                place_id=place_id,
                fields=["name", "formatted_address", "geometry", "types"]
            )
            
            # Get nearby attractions
            attractions = self.gmaps.places_nearby(
                location=place_details["result"]["geometry"]["location"],
                radius=50000,  # 50km radius
                type="tourist_attraction"
            )
            
            # Get major cities in the region
            cities = self.gmaps.places_nearby(
                location=place_details["result"]["geometry"]["location"],
                radius=100000,  # 100km radius
                type="locality"
            )
            
            return {
                "success": True,
                "message": f"Found information about {destination}",
                "data": {
                    "destination": place_details["result"],
                    "attractions": attractions.get("results", [])[:5],  # Top 5 attractions
                    "cities": cities.get("results", [])[:3]  # Top 3 cities
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting destination info: {str(e)}",
                "data": None
            }
    
    async def _get_restaurants(self, query: str) -> Dict[str, Any]:
        """Get restaurant recommendations for a location."""
        try:
            # Extract location from query
            location = query.split("near")[-1].strip()
            
            # Search for the location
            places_result = self.gmaps.places(
                query=location,
                type="locality"
            )
            
            if not places_result.get("results"):
                return {
                    "success": False,
                    "message": f"Could not find location: {location}",
                    "data": None
                }
            
            # Get the first result
            place = places_result["results"][0]
            
            # Search for restaurants
            restaurants = self.gmaps.places_nearby(
                location=place["geometry"]["location"],
                radius=2000,  # 2km radius
                type="restaurant",
                rank_by="rating"
            )
            
            # Get details for each restaurant
            restaurant_details = []
            for restaurant in restaurants.get("results", [])[:5]:  # Top 5 restaurants
                details = self.gmaps.place(
                    place_id=restaurant["place_id"],
                    fields=["name", "formatted_address", "rating", "price_level", "opening_hours", "website"]
                )
                restaurant_details.append(details["result"])
            
            return {
                "success": True,
                "message": f"Found restaurants near {location}",
                "data": restaurant_details
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting restaurants: {str(e)}",
                "data": None
            }
    
    async def _process_general_query(self, query: str) -> Dict[str, Any]:
        """Process general location-based queries."""
        try:
            # Use the base agent's process method for general queries
            return await super().process({
                "messages": [HumanMessage(content=query)],
                "context": {"intent": "general_query"}
            })
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing query: {str(e)}",
                "data": None
            } 