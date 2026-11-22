from app.routes.auth_routes import auth_bp
from app.routes.budget_routes import budget_bp
from app.routes.consumption_routes import consumption_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.feedback_routes import feedback_bp
from app.routes.grocery_routes import grocery_bp
from app.routes.household_routes import household_bp
from app.routes.inventory_routes import inventory_bp
from app.routes.prediction_routes import prediction_bp
from app.routes.purchase_routes import purchase_bp
from app.routes.ai_routes import ai_bp

ALL_BLUEPRINTS = [
    auth_bp,
    household_bp,
    grocery_bp,
    inventory_bp,
    purchase_bp,
    consumption_bp,
    prediction_bp,
    budget_bp,
    dashboard_bp,
    feedback_bp,
    ai_bp,
]
