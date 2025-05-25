from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from app.tools.base import BaseTravelTool
from app.core.logging import logger

class BudgetItem(BaseModel):
    """Model for budget item data."""
    category: str = Field(..., description="Expense category")
    amount: float = Field(..., description="Amount in KRW")
    currency: str = Field(default="KRW", description="Currency code")
    date: datetime = Field(..., description="Date of expense")
    description: Optional[str] = Field(None, description="Expense description")
    exchange_rate: Optional[float] = Field(default=1.0, description="Exchange rate to KRW")

class Budget(BaseModel):
    """Model for travel budget data."""
    total_budget: float = Field(..., description="Total budget amount in KRW")
    base_currency: str = Field(default="KRW", description="Base currency code")
    start_date: datetime = Field(..., description="Start date of travel")
    end_date: datetime = Field(..., description="End date of travel")
    items: List[BudgetItem] = Field(default_factory=list, description="Budget items")
    categories: Dict[str, float] = Field(default_factory=dict, description="Budget by category")

class BudgetTool(BaseTravelTool):
    """Tool for managing travel budgets."""
    
    name: str = "budget"
    description: str = "Track and manage travel expenses and budgets"
    
    def __init__(self):
        super().__init__(
            name=self.name,
            description=self.description
        )
        self.budgets: Dict[str, Budget] = {}

    def _run(
        self,
        total_budget: float,
        base_currency: str = "KRW",
        start_date: str = None,
        end_date: str = None,
        items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a new travel budget."""
        try:
            # Validate dates
            start = datetime.fromisoformat(start_date) if start_date else datetime.now()
            end = datetime.fromisoformat(end_date) if end_date else start + timedelta(days=7)
            
            if start >= end:
                raise ValueError("Start date must be before end date")

            # Create budget
            budget = Budget(
                total_budget=total_budget,
                base_currency=base_currency,
                start_date=start,
                end_date=end
            )

            # Add items if provided
            if items:
                for item in items:
                    budget_item = BudgetItem(
                        category=item["category"],
                        amount=item["amount"],
                        currency=item.get("currency", "KRW"),
                        date=datetime.fromisoformat(item["date"]),
                        description=item.get("description"),
                        exchange_rate=item.get("exchange_rate", 1.0)
                    )
                    budget.items.append(budget_item)

            # Calculate category totals
            for item in budget.items:
                amount_in_krw = item.amount * item.exchange_rate
                budget.categories[item.category] = budget.categories.get(item.category, 0) + amount_in_krw

            # Store budget
            budget_id = f"{start_date}_{end_date}"
            self.budgets[budget_id] = budget

            logger.info(f"Created budget for {start_date} to {end_date}")
            return self.format_output(budget.dict())

        except Exception as e:
            return self.handle_error(e)

    async def _arun(
        self,
        total_budget: float,
        base_currency: str = "KRW",
        start_date: str = None,
        end_date: str = None,
        items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Async implementation of budget creation."""
        return self._run(total_budget, base_currency, start_date, end_date, items)

    def add_expense(
        self,
        budget_id: str,
        category: str,
        amount: float,
        currency: str = "KRW",
        date: str = None,
        description: Optional[str] = None,
        exchange_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """Add an expense to the budget."""
        try:
            if budget_id not in self.budgets:
                raise ValueError(f"Budget {budget_id} not found")

            budget = self.budgets[budget_id]
            
            # Create budget item
            item = BudgetItem(
                category=category,
                amount=amount,
                currency=currency,
                date=datetime.fromisoformat(date) if date else datetime.now(),
                description=description,
                exchange_rate=exchange_rate or 1.0
            )

            # Add item to budget
            budget.items.append(item)

            # Update category total
            amount_in_krw = amount * item.exchange_rate
            budget.categories[category] = budget.categories.get(category, 0) + amount_in_krw

            logger.info(f"Added expense to budget {budget_id}")
            return self.format_output(budget.dict())

        except Exception as e:
            return self.handle_error(e)

    def get_budget_summary(
        self,
        budget_id: str
    ) -> Dict[str, Any]:
        """Get a summary of the budget."""
        try:
            if budget_id not in self.budgets:
                raise ValueError(f"Budget {budget_id} not found")

            budget = self.budgets[budget_id]
            
            # Calculate totals
            total_spent = sum(item.amount * item.exchange_rate for item in budget.items)
            remaining = budget.total_budget - total_spent
            
            summary = {
                "total_budget": budget.total_budget,
                "total_spent": total_spent,
                "remaining": remaining,
                "currency": "KRW",
                "categories": budget.categories,
                "items": [item.dict() for item in budget.items]
            }

            return self.format_output(summary)

        except Exception as e:
            return self.handle_error(e)

    def update_exchange_rates(
        self,
        budget_id: str,
        rates: Dict[str, float]
    ) -> Dict[str, Any]:
        """Update exchange rates for the budget."""
        try:
            if budget_id not in self.budgets:
                raise ValueError(f"Budget {budget_id} not found")

            budget = self.budgets[budget_id]
            
            # Update exchange rates
            for item in budget.items:
                if item.currency in rates:
                    item.exchange_rate = rates[item.currency]

            # Recalculate category totals
            budget.categories.clear()
            for item in budget.items:
                amount_in_krw = item.amount * item.exchange_rate
                budget.categories[item.category] = budget.categories.get(item.category, 0) + amount_in_krw

            logger.info(f"Updated exchange rates for budget {budget_id}")
            return self.format_output(budget.dict())

        except Exception as e:
            return self.handle_error(e) 