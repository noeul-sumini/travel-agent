from typing import Dict, Any, List, Optional
import aiohttp
from pydantic import BaseModel, Field
from app.tools.base import BaseTravelTool
from app.core.config import get_settings
from app.core.logging import logger

class LocationData(BaseModel):
    """Model for location data."""
    name: str = Field(..., description="Location name")
    address: str = Field(..., description="Full address")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    place_id: str = Field(..., description="Google Places ID")
    types: List[str] = Field(default_factory=list, description="Location types")
    rating: Optional[float] = Field(None, description="Location rating")
    photos: List[str] = Field(default_factory=list, description="Photo references")
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="Opening hours")
    website: Optional[str] = Field(None, description="Website URL")
    phone: Optional[str] = Field(None, description="Phone number")

class MapsTool(BaseTravelTool):
    """Tool for getting location information and directions."""
    
    name: str = "maps"
    description: str = "Get location information and directions using Google Maps API"
    
    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description
        )
        self.settings = get_settings()
        self.api_key = self.settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"

    async def _arun(
        self,
        query: str,
        location_type: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search for a location."""
        try:
            # Make API request
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/place/textsearch/json"
                params = {
                    "key": self.api_key,
                    "query": query,
                    "type": location_type if location_type else None,
                    "fields": ",".join(fields) if fields else None
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Google Maps API error: {response.status}")
                    
                    data = await response.json()
                    
                    if data["status"] != "OK":
                        raise Exception(f"Google Maps API error: {data['status']}")
                    
                    # Extract location data
                    place = data["results"][0]
                    location_data = LocationData(
                        name=place["name"],
                        address=place["formatted_address"],
                        latitude=place["geometry"]["location"]["lat"],
                        longitude=place["geometry"]["location"]["lng"],
                        place_id=place["place_id"],
                        types=place["types"],
                        rating=place.get("rating"),
                        photos=[photo["photo_reference"] for photo in place.get("photos", [])],
                        opening_hours=place.get("opening_hours"),
                        website=place.get("website"),
                        phone=place.get("formatted_phone_number")
                    )

                    logger.info(f"Retrieved location data for {query}")
                    return self.format_output(location_data.dict())

        except Exception as e:
            return self.handle_error(e)

    def _run(
        self,
        query: str,
        location_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sync implementation of location search."""
        raise NotImplementedError("Maps tool only supports async execution")

    async def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        departure_time: Optional[str] = None,
        arrival_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get directions between two locations."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/directions/json"
                params = {
                    "key": self.api_key,
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "alternatives": "true"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Google Maps API error: {response.status}")
                    
                    data = await response.json()
                    
                    if data["status"] != "OK":
                        raise Exception(f"Google Maps API error: {data['status']}")
                    
                    routes = []
                    for route in data["routes"]:
                        route_info = {
                            "summary": route["summary"],
                            "distance": route["legs"][0]["distance"]["text"],
                            "duration": route["legs"][0]["duration"]["text"],
                            "steps": [
                                {
                                    "instruction": step["html_instructions"],
                                    "distance": step["distance"]["text"],
                                    "duration": step["duration"]["text"],
                                    "mode": step.get("travel_mode", mode)
                                }
                                for step in route["legs"][0]["steps"]
                            ]
                        }
                        routes.append(route_info)

                    return self.format_output({
                        "routes": routes,
                        "best_route": routes[0]
                    })

        except Exception as e:
            return self.handle_error(e)

    async def get_nearby_places(
        self,
        location: str,
        radius: int = 1000,
        place_type: Optional[str] = None,
        keyword: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get nearby places around a location."""
        try:
            # First get the location coordinates
            location_data = await self._arun(location)
            if location_data["status"] != "success":
                raise Exception("Failed to get location coordinates")

            lat = location_data["data"]["latitude"]
            lng = location_data["data"]["longitude"]

            # Then search for nearby places
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/place/nearbysearch/json"
                params = {
                    "key": self.api_key,
                    "location": f"{lat},{lng}",
                    "radius": radius,
                    "type": place_type if place_type else None,
                    "keyword": keyword if keyword else None,
                    "minprice": 0,
                    "maxprice": 4,
                    "opennow": True
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Google Maps API error: {response.status}")
                    
                    data = await response.json()
                    
                    if data["status"] != "OK":
                        raise Exception(f"Google Maps API error: {data['status']}")
                    
                    places = []
                    for place in data["results"]:
                        if min_rating and place.get("rating", 0) < min_rating:
                            continue
                            
                        place_info = {
                            "name": place["name"],
                            "address": place.get("vicinity"),
                            "rating": place.get("rating"),
                            "types": place["types"],
                            "place_id": place["place_id"],
                            "location": place["geometry"]["location"],
                            "photos": [photo["photo_reference"] for photo in place.get("photos", [])],
                            "opening_hours": place.get("opening_hours"),
                            "price_level": place.get("price_level")
                        }
                        places.append(place_info)

                    return self.format_output({
                        "places": places,
                        "total": len(places),
                        "location": location_data["data"]
                    })

        except Exception as e:
            return self.handle_error(e)

    def format_output(self, data: Any) -> Dict[str, Any]:
        """Format the output response."""
        return {
            "status": "success",
            "data": data
        }

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors and format error response."""
        error_message = str(error)
        logger.error(f"Maps operation failed: {error_message}")
        return {
            "status": "error",
            "error": error_message
        } 