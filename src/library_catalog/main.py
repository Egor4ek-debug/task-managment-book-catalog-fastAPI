from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, status
from starlette.responses import JSONResponse

from .app_state import AppState
from .config import Config
from .core.exceptions import ApiClientError, RepositoryError
from .core.logging import setup_logging
from .models.book import Book, BookCreate
from .services.book_services import BookService

logger = setup_logging()
config = Config()
app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекст жизненного цикла приложения"""
    # Инициализация состояния приложения
    await app_state.initialize()

    # Выполняем резервное копирование при запуске
    try:
        from .repositories.json_repository import JsonRepository
        backup_repo = JsonRepository("backup_books.json")
        await app_state.book_service.backup_books(backup_repo)
        logger.info("Initial backup completed successfully")
    except Exception as e:
        logger.error(f"Initial backup failed: {str(e)}")

    yield

    # Завершение работы приложения
    await app_state.shutdown()


app = FastAPI(lifespan=lifespan)


# Функция для получения сервиса книг
def get_book_service() -> BookService:
    return app_state.book_service


@app.exception_handler(RepositoryError)
async def handle_repository_error(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error"}
    )


@app.exception_handler(ApiClientError)
async def handle_api_client_error(request, exc):
    return JSONResponse(
        status_code=502,
        content={"detail": "External service error"}
    )


@app.get("/")
async def read_root():
    return {
        "message": "Добро пожаловать в систему управления библиотекой!",
        "storage": config.STORAGE_TYPE,
        "features": ["CRUD для книг", "Обогащение данных из Open Library API"],
        "openlibrary": "https://openlibrary.org"
    }


@app.get("/books", response_model=List[Book], summary="Получить список книг")
async def get_books(
        genre: Optional[str] = None,
        available: Optional[bool] = None,
        author: Optional[str] = None,
        book_service: BookService = Depends(get_book_service)
):
    return await book_service.get_all_books(genre, available, author)


@app.get("/books/{book_id}", response_model=Book, summary="Получить книгу по ID")
async def get_book(
        book_id: int,
        book_service: BookService = Depends(get_book_service)
):
    return await book_service.get_book_by_id(book_id)


@app.post("/books",
          response_model=Book,
          status_code=status.HTTP_201_CREATED,
          summary="Добавить новую книгу")
async def add_book(
        book: BookCreate,
        book_service: BookService = Depends(get_book_service)
):
    return await book_service.add_book(book)


@app.put("/books/{book_id}", response_model=Book, summary="Обновить информацию о книге")
async def update_book(
        book_id: int,
        book_update: BookCreate,
        book_service: BookService = Depends(get_book_service)
):
    return await book_service.update_book(book_id, book_update)


@app.delete("/books/{book_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Удалить книгу из каталога")
async def delete_book(book_id: int, book_service: BookService = Depends(get_book_service)):
    await book_service.delete_book(book_id)
    return
