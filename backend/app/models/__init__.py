"""Import every model so SQLAlchemy and Flask-Migrate can see all tables."""
from app.models.user import User
from app.models.household import Household
from app.models.grocery_item import GroceryItem
from app.models.inventory import Inventory, StockMovement
from app.models.purchase import Purchase
from app.models.consumption import Consumption
from app.models.recommendation import Recommendation, RecommendationItem
from app.models.feedback import Feedback

__all__ = [
    "User",
    "Household",
    "GroceryItem",
    "Inventory",
    "StockMovement",
    "Purchase",
    "Consumption",
    "Recommendation",
    "RecommendationItem",
    "Feedback",
]
