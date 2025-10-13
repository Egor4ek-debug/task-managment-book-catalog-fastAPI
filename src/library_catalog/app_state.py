from .api_clients.openlibrary_client import OpenLibraryClient
from .config import Config
from .core.exceptions import RepositoryError
from .core.logging import setup_logging
from .repositories.in_memory_repository import InMemoryRepository
from .repositories.json_repository import JsonRepository
from .repositories.jsonbin_repository import JsonBinRepository
from .repositories.postgres_repository import PostgresRepository

logger = setup_logging()
config = Config()


class AppState:
    def __init__(self):
        self.openlibrary_client = OpenLibraryClient()
        self.repo = None
        self.book_service = None

    async def initialize(self):
        """Инициализация состояния приложения"""
        try:
            if config.STORAGE_TYPE == "postgres":
                # from alembic.config import Config
                # from alembic import command
                # alembic_cfg = Config("alembic.ini")
                # command.upgrade(alembic_cfg, "head")
                self.repo = PostgresRepository(config.DATABASE_URL)
                await self.repo.connect()
            elif config.STORAGE_TYPE == "json":
                self.repo = JsonRepository("books.json")
            elif config.STORAGE_TYPE == "jsonbin":
                self.repo = JsonBinRepository(config.JSONBIN_API_KEY, config.JSONBIN_BIN_ID)
            else:
                self.repo = InMemoryRepository()

            self.repo.api_client = self.openlibrary_client
            logger.info(f"Using {config.STORAGE_TYPE} storage")
        except RepositoryError as e:
            logger.error(f"Storage error: {str(e)}")
            self.repo = InMemoryRepository()
            self.repo.api_client = self.openlibrary_client
            logger.warning("Fallback to in-memory storage")

        from .services.book_services import BookService
        self.book_service = BookService(self.repo)

    async def shutdown(self):
        """Очистка ресурсов при завершении"""
        if self.repo and hasattr(self.repo, 'close'):
            await self.repo.close()
