from typing import Dict, Any, Optional
import aiohttp
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.tools.base import BaseTravelTool
from app.core.config import get_settings
from app.core.logging import logger

class WeatherData(BaseModel):
    """Model for weather data."""
    location: str = Field(..., description="Location name")
    date: datetime = Field(..., description="Date of weather forecast")
    temperature: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(..., description="Weather condition")
    humidity: float = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed in km/h")
    precipitation: float = Field(..., description="Precipitation probability")

class WeatherTool(BaseTravelTool):
    """Tool for getting weather information."""
    
    name: str = "weather"
    description: str = "Get weather forecasts for travel destinations"
    
    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description
        )
        self.settings = get_settings()
        self.api_key = self.settings.WEATHER_API_KEY
        self.base_url = "https://api.weatherapi.com/v1"

    async def _arun(
        self,
        location: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get weather forecast for a location."""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")

            # Validate date
            forecast_date = datetime.strptime(date, "%Y-%m-%d")
            if forecast_date < datetime.now():
                raise ValueError("Cannot get weather for past dates")

            # Make API request
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/forecast.json"
                params = {
                    "key": self.api_key,
                    "q": location,
                    "dt": date,
                    "aqi": "no"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Weather API error: {response.status}")
                    
                    data = await response.json()
                    
                    # Extract relevant weather data
                    forecast = data["forecast"]["forecastday"][0]
                    day = forecast["day"]
                    
                    weather_data = WeatherData(
                        location=data["location"]["name"],
                        date=datetime.strptime(date, "%Y-%m-%d"),
                        temperature=day["avgtemp_c"],
                        condition=day["condition"]["text"],
                        humidity=day["avghumidity"],
                        wind_speed=day["maxwind_kph"],
                        precipitation=day["daily_chance_of_rain"]
                    )

                    logger.info(f"Retrieved weather data for {location}")
                    return self.format_output(weather_data.dict())

        except Exception as e:
            return self.handle_error(e)

    def _run(
        self,
        location: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sync implementation of weather forecast."""
        raise NotImplementedError("Weather tool only supports async execution")

    async def get_forecast(
        self,
        location: str,
        days: int = 3
    ) -> Dict[str, Any]:
        """Get weather forecast for multiple days."""
        try:
            forecasts = []
            for i in range(days):
                date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                forecast = await self._arun(location, date)
                if forecast["status"] == "success":
                    forecasts.append(forecast["data"])

            return self.format_output(forecasts)

        except Exception as e:
            return self.handle_error(e) 