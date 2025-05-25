from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.tools.base import BaseTravelTool
from app.core.logging import logger

class TravelPlan(BaseModel):
    """Model for travel plan data."""
    destination: str = Field(..., description="Travel destination")
    start_date: datetime = Field(..., description="Start date of the trip")
    end_date: datetime = Field(..., description="End date of the trip")
    activities: List[Dict[str, Any]] = Field(default_factory=list, description="Planned activities")
    accommodations: List[Dict[str, Any]] = Field(default_factory=list, description="Accommodation details")
    transportation: List[Dict[str, Any]] = Field(default_factory=list, description="Transportation details")
    budget: Dict[str, float] = Field(default_factory=dict, description="Budget breakdown")
    notes: List[str] = Field(default_factory=list, description="Additional notes")

class TravelPlanningTool(BaseTravelTool):
    """Tool for creating and managing travel plans."""
    
    name: str = "travel_planning"
    description: str = "Create and manage travel itineraries with detailed planning"
    
    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description
        )
        self.plans: Dict[str, TravelPlan] = {}

    def _run(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new travel plan."""
        try:
            # Validate dates
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            if start >= end:
                raise ValueError("Start date must be before end date")

            # Create plan
            plan = TravelPlan(
                destination=destination,
                start_date=start,
                end_date=end
            )

            # Add preferences if provided
            if preferences:
                if "activities" in preferences:
                    plan.activities = preferences["activities"]
                if "accommodations" in preferences:
                    plan.accommodations = preferences["accommodations"]
                if "transportation" in preferences:
                    plan.transportation = preferences["transportation"]
                if "budget" in preferences:
                    plan.budget = preferences["budget"]
                if "notes" in preferences:
                    plan.notes = preferences["notes"]

            # Store plan
            plan_id = f"{destination}_{start_date}_{end_date}"
            self.plans[plan_id] = plan

            logger.info(f"Created travel plan for {destination}")
            return self.format_output(plan.dict())

        except Exception as e:
            return self.handle_error(e)

    async def _arun(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async implementation of travel plan creation."""
        return self._run(destination, start_date, end_date, preferences)

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a travel plan by ID."""
        if plan_id in self.plans:
            return self.format_output(self.plans[plan_id].dict())
        return None

    def update_plan(
        self,
        plan_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing travel plan."""
        if plan_id not in self.plans:
            return None

        plan = self.plans[plan_id]
        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        return self.format_output(plan.dict())

    def delete_plan(self, plan_id: str) -> bool:
        """Delete a travel plan."""
        if plan_id in self.plans:
            del self.plans[plan_id]
            return True
        return False 