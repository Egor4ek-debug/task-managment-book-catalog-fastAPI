# dependencies.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends

from .api_clients.openlibrary_client import OpenLibraryClient
from .config import Config
from .core.base_repository import BookRepositoryBase
from .core.exceptions import RepositoryError
from .core.logging import setup_logging
from .repositories.in_memory_repository import InMemoryRepository
from .repositories.json_repository import JsonRepository
from .repositories.jsonbin_repository import JsonBinRepository
from .repositories.postgres_repository import PostgresRepository
from .services.book_services import BookService

logger = setup_logging()
config = Config()


def get_openlibrary_client() -> OpenLibraryClient:
    """Зависимость для клиента OpenLibrary"""
    return OpenLibraryClient()


@asynccontextmanager
async def get_repository(openlibrary_client: OpenLibraryClient = Depends(get_openlibrary_client)) -> AsyncGenerator[
    BookRepositoryBase, None]:
    """Асинхронный генератор для репозитория книг"""
    repo = None
    try:
        if config.STORAGE_TYPE == "postgres":
            repo = PostgresRepository(config.DATABASE_URL)
            # Явно ожидаем инициализацию пула подключений
            await repo.connect()
        elif config.STORAGE_TYPE == "json":
            repo = JsonRepository("books.json")
        elif config.STORAGE_TYPE == "jsonbin":
            repo = JsonBinRepository(config.JSONBIN_API_KEY, config.JSONBIN_BIN_ID)
        else:
            repo = InMemoryRepository()

        repo.api_client = openlibrary_client
        logger.info(f"Using {config.STORAGE_TYPE} storage")
        yield repo
    except RepositoryError as e:
        logger.error(f"Storage error: {str(e)}")
        repo = InMemoryRepository()
        repo.api_client = openlibrary_client
        logger.warning("Fallback to in-memory storage")
        yield repo
    finally:
        if repo and hasattr(repo, 'close'):
            await repo.close()


def get_book_service(repo: BookRepositoryBase = Depends(get_repository)) -> BookService:
    """Зависимость для сервиса книг"""
    return BookService(repo)
