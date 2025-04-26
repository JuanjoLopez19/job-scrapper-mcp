# shared/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / "user_data"
OUTPUT_DIR = BASE_DIR / "outputs"

# Ensure directories exist
os.makedirs(USER_DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# File paths
CV_FILE_PATH = USER_DATA_DIR / "cv.txt"

# API Keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
BRAVE_SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# LLM Configuration
LLM_MODEL = "gpt-4o-mini"  # or any other model

# LLM provider
LLM_PROVIDER = "openai"  # or "ollama" for local models

# Search provider
SEARCH_PROVIDER = "brave"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"