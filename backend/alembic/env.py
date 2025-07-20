import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config object
config = context.config

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

# Make sure app directory is on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ✅ Use the SYNC database URL just for Alembic
db_url = os.getenv("DATABASE_URL_SYNC")  # This must be set in .env
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Import your SQLAlchemy Base and models
from app.database import Base
from app.models.user import User
from app.models.user_settings import UserSettings
from app.models.location import LocationEntry
from app.models.quiz import QuizQuestion
from app.models.quiz_answer import QuizAnswer
from app.models.quiz_submission import QuizSubmission
from app.models.lesson import Lesson
from app.models.star_watchlist import StarWatchlist

# Metadata for autogenerate support
target_metadata = Base.metadata

# Optional logging config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Migration functions
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to DB)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# Decide mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()