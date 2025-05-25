from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.tools.base import BaseTravelTool
from app.core.config import get_settings
from app.core.logging import logger

class FlightData(BaseModel):
    """Model for flight data."""
    airline: str = Field(..., description="Airline name")
    flight_number: str = Field(..., description="Flight number")
    departure_airport: str = Field(..., description="Departure airport code")
    arrival_airport: str = Field(..., description="Arrival airport code")
    departure_time: datetime = Field(..., description="Departure time")
    arrival_time: datetime = Field(..., description="Arrival time")
    price: float = Field(..., description="Flight price")
    currency: str = Field(..., description="Price currency")
    stops: int = Field(..., description="Number of stops")
    duration: str = Field(..., description="Flight duration")

class FlightsTool(BaseTravelTool):
    """Tool for searching and booking flights."""
    
    name: str = "flights"
    description: str = "Search and book flights using Skyscanner API"
    
    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description
        )
        self.settings = get_settings()
        self.api_key = self.settings.SKYSCANNER_API_KEY
        self.base_url = "https://skyscanner-api.p.rapidapi.com/v1"

    async def _arun(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        cabin_class: str = "economy"
    ) -> Dict[str, Any]:
        """Search for flights."""
        try:
            # Validate dates
            dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
            if dep_date < datetime.now():
                raise ValueError("Departure date cannot be in the past")

            if return_date:
                ret_date = datetime.strptime(return_date, "%Y-%m-%d")
                if ret_date <= dep_date:
                    raise ValueError("Return date must be after departure date")

            # Make API request
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/flights/search"
                headers = {
                    "X-RapidAPI-Key": self.api_key,
                    "X-RapidAPI-Host": "skyscanner-api.p.rapidapi.com"
                }
                params = {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "adults": adults,
                    "cabin_class": cabin_class
                }
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Skyscanner API error: {response.status}")
                    
                    data = await response.json()
                    
                    # Extract flight data
                    flights = []
                    for itinerary in data.get("itineraries", []):
                        for leg in itinerary.get("legs", []):
                            flight = FlightData(
                                airline=leg["carriers"]["marketing"][0]["name"],
                                flight_number=leg["carriers"]["marketing"][0]["flightNumber"],
                                departure_airport=leg["origin"]["iata"],
                                arrival_airport=leg["destination"]["iata"],
                                departure_time=datetime.fromisoformat(leg["departure"]),
                                arrival_time=datetime.fromisoformat(leg["arrival"]),
                                price=itinerary["pricing"]["total"],
                                currency=itinerary["pricing"]["currency"],
                                stops=len(leg.get("stops", [])),
                                duration=leg["duration"]
                            )
                            flights.append(flight.dict())

                    logger.info(f"Found {len(flights)} flights from {origin} to {destination}")
                    return self.format_output(flights)

        except Exception as e:
            return self.handle_error(e)

    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        cabin_class: str = "economy"
    ) -> Dict[str, Any]:
        """Sync implementation of flight search."""
        raise NotImplementedError("Flights tool only supports async execution")

    async def get_airport_code(
        self,
        city: str
    ) -> Dict[str, Any]:
        """Get airport code for a city."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/airports/search"
                headers = {
                    "X-RapidAPI-Key": self.api_key,
                    "X-RapidAPI-Host": "skyscanner-api.p.rapidapi.com"
                }
                params = {"query": city}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Skyscanner API error: {response.status}")
                    
                    data = await response.json()
                    
                    if not data.get("airports"):
                        raise Exception(f"No airports found for {city}")
                    
                    airport = data["airports"][0]
                    return self.format_output({
                        "city": airport["city"],
                        "airport": airport["name"],
                        "code": airport["iata"]
                    })

        except Exception as e:
            return self.handle_error(e)

    async def get_price_alerts(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        target_price: float = 0.0
    ) -> Dict[str, Any]:
        """Set up price alerts for flights."""
        try:
            # First search for current prices
            flights = await self._arun(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date
            )

            if flights["status"] != "success":
                raise Exception("Failed to get flight prices")

            # Find the cheapest flight
            cheapest_flight = min(
                flights["data"],
                key=lambda x: x["price"]
            )

            # Set up price alert if target price is specified
            if target_price > 0:
                if cheapest_flight["price"] <= target_price:
                    return self.format_output({
                        "message": f"Current price (${cheapest_flight['price']}) is already below target price (${target_price})",
                        "flight": cheapest_flight
                    })
                else:
                    return self.format_output({
                        "message": f"Price alert set for ${target_price}. Current price is ${cheapest_flight['price']}",
                        "flight": cheapest_flight
                    })
            else:
                return self.format_output({
                    "message": f"Current lowest price is ${cheapest_flight['price']}",
                    "flight": cheapest_flight
                })

        except Exception as e:
            return self.handle_error(e) 