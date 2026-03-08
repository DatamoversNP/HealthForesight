from logging.config import fileConfig
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add src directory to Python path for imports
# alembic.ini has prepend_sys_path = . which should add current directory
# But we need to explicitly add src and common paths
current_dir = Path(__file__).parent.parent  # apps/api
src_dir = current_dir / "src"
common_dir = current_dir.parent.parent / "packages" / "common" / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(common_dir) not in sys.path:
    sys.path.insert(0, str(common_dir))

# Import all models for autogenerate
from uepi_api.models import *  # noqa: F401, F403
from uepi_api.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Get database URL from environment - PostgreSQL only"""
    from uepi_api.config import get_settings
    
    # Use the same configuration as the main app
    settings = get_settings()
    db_url = settings.database.url
    
    # Validate PostgreSQL connection string
    if not db_url.startswith("postgresql") and not db_url.startswith("postgresql+psycopg2"):
        raise ValueError(
            f"Invalid database URL for Alembic: expected PostgreSQL connection string, "
            f"got: {db_url[:50]}...\n"
            "This application requires PostgreSQL. Update DATABASE_URL environment variable."
        )
    
    return db_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
