"""Application factory: creates and configures the Flask app."""
import logging

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.extensions import cors, db, jwt, limiter, migrate
from app.utils.responses import error
from app.utils.validators import ValidationError

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    # Only the configured frontend may call the API with cookies.
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": [app.config["FRONTEND_ORIGIN"]]}},
        supports_credentials=True,
    )

    from app import models  # noqa: F401  (register tables)
    from app.routes import ALL_BLUEPRINTS

    for blueprint in ALL_BLUEPRINTS:
        app.register_blueprint(blueprint)

    register_error_handlers(app)
    register_jwt_handlers()
    register_cli(app)

    @app.get("/api/health")
    def health():
        return {"success": True, "message": "API is running"}

    return app


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation(exc):
        db.session.rollback()
        return error(exc.message, exc.status_code)

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(exc):
        db.session.rollback()  # undo the whole transaction
        logger.exception("Database error")  # logged server-side only
        return error("A database error occurred. No changes were saved. Please try again.", 500)

    @app.errorhandler(HTTPException)
    def handle_http(exc):
        if exc.code == 429:
            return error("Too many attempts. Please wait a minute and try again.", 429)
        messages = {404: "Resource not found.", 405: "Method not allowed."}
        return error(messages.get(exc.code, exc.description), exc.code)

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        db.session.rollback()
        logger.exception("Unexpected error")
        # Never send stack traces to users.
        return error("Something went wrong on the server.", 500)


def register_jwt_handlers():
    @jwt.expired_token_loader
    def expired(_header, _payload):
        return error("Your session has expired. Please log in again.", 401)

    @jwt.invalid_token_loader
    def invalid(_reason):
        return error("Invalid session. Please log in again.", 401)

    @jwt.unauthorized_loader
    def missing(reason):
        if "CSRF" in reason:
            return error("Missing security token. Please refresh the page.", 401)
        return error("Please log in to continue.", 401)


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create all tables (alternative to `flask db upgrade`)."""
        db.create_all()
        print("Database tables created.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Load clearly-labelled DEMONSTRATION data."""
        from app.demo_data import seed

        email, password = seed()
        print(f"Demo data loaded. Log in with {email} / {password}")
