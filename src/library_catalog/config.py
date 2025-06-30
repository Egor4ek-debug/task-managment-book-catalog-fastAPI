import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "postgres")
    DATABASE_URL = os.getenv("DATABASE_URL")
    JSONBIN_API_KEY = os.getenv("JSONBIN_API_KEY")
    JSONBIN_BIN_ID = os.getenv("JSONBIN_BIN_ID")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")