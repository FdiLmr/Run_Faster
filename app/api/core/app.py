from flask import Flask
from flask_session import Session
from sqlalchemy import inspect, text
import logging

from .config import config
from database import init_db, db

logger = logging.getLogger(__name__)


def create_app(config_name="default"):
    """Create and configure the Flask application."""
    # Set template and static folder paths relative to the main app directory
    import os

    template_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "templates")
    )
    static_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "static")
    )

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions
    Session(app)
    init_db(app)

    # Create database tables
    with app.app_context():
        # Import models after database initialization to register them with SQLAlchemy
        import models
        db.create_all()
        create_required_tables()

    # Register blueprints
    from routes import auth, dashboard, data, api

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(data.bp)
    app.register_blueprint(api.bp)

    # Register template filters and context processors
    from .filters import register_filters
    from .utils import register_context_processors

    register_filters(app)
    register_context_processors(app)

    return app


def create_required_tables():
    """Create required database tables and initialize data."""
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    logger.info(f"Current tables: {existing_tables}")

    # Force create all tables from models
    db.create_all()

    # Initialize processing_status if empty
    if "processing_status" in existing_tables:
        with db.engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM processing_status")
            ).scalar()
            logger.info(f"Processing status entries: {result}")

    # Initialize daily_limit if it doesn't exist
    if "daily_limit" not in existing_tables:
        with db.engine.connect() as conn:
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS daily_limit (
                    daily INTEGER NOT NULL
                )
            """
                )
            )
            conn.execute(text("INSERT INTO daily_limit (daily) VALUES (0)"))
            conn.commit()

    # Make sure the metadata_pbs table exists
    if "metadata_pbs" not in existing_tables:
        logger.info("Creating metadata_pbs table")
        db.create_all()
    else:
        # Check if the uniqueness constraint exists
        with db.engine.connect() as conn:
            constraint_query = text(
                """
                SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE table_name = 'metadata_pbs' 
                AND constraint_name = 'uix_athlete_id_distance_category'
            """
            )
            has_constraint = conn.execute(constraint_query).scalar() > 0

            if not has_constraint:
                logger.info("Recreating metadata_pbs table with uniqueness constraint")
                conn.execute(text("DROP TABLE metadata_pbs"))
                conn.commit()
                db.create_all()
                logger.info("metadata_pbs table recreated successfully")

    # Make sure the race_predictions table exists
    if "race_predictions" not in existing_tables:
        logger.info("Creating race_predictions table")
        db.create_all()

    # Log created tables
    updated_tables = inspect(db.engine).get_table_names()
    logger.info(f"Available tables after creation: {updated_tables}")
