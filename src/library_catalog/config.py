import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "postgres")
    DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)
    JSONBIN_API_KEY = os.getenv("JSONBIN_API_KEY")
    JSONBIN_BIN_ID = os.getenv("JSONBIN_BIN_ID")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    BASE_URL_OPEN_LIBRARY = os.getenv("BASE_URL_OPEN_LIBRARY")
    BASE_URL_JSONBIN = os.getenv("BASE_URL_JSONBIN")