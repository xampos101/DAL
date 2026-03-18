"""Load settings from environment. Uses python-dotenv for .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
ACCESS_TOKEN: str = os.getenv("ACCESS_TOKEN", "")
