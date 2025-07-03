import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import SQLAlchemy base and models
from app.database import Base
from app.models import (
    user,
    location,
    quiz_question,
    quiz_submission,
    quiz_answer,
    user_settings,
    star_watchlist,
    lesson
)

# This tells Alembic which models to generate migrations for
target_metadata = Base.metadata

# Optional: override sqlalchemy.url from .env
from alembic import context
if config := context.config:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)