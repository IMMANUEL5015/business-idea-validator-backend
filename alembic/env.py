from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Load our app's settings and models
from helpers.config import settings
from database.db import Base
import database.models  # noqa: F401 — ensures all models are registered on Base.metadata

config = context.config

# Inject the real database URL from our .env file
config.set_main_option("sqlalchemy.url", settings.database_url)

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at our models so autogenerate can diff against them
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (outputs SQL to stdout)."""
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
    """Run migrations against a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()