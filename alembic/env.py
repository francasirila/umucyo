import sys
import os
from logging.config import fileConfig

from alembic import context

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import Base, SQLALCHEMY_DATABASE_URL

config = context.config

# Set the URL dynamically from the .env file
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
