from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status
from starlette.responses import JSONResponse

from .api_clients.openlibrary_client import OpenLibraryClient
from .config import Config
from .core.exceptions import ApiClientError, RepositoryError
from .core.logging import setup_logging
from .models.book import Book, BookCreate
from .repositories.in_memory_repository import InMemoryRepository
from .repositories.json_repository import JsonRepository
from .repositories.jsonbin_repository import JsonBinRepository
from .repositories.postgres_repository import PostgresRepository

logger = setup_logging()
config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_client = OpenLibraryClient()

    try:
        if config.STORAGE_TYPE == "postgres":
            repo = PostgresRepository(config.DATABASE_URL)
            await repo.connect()
        elif config.STORAGE_TYPE == "json":
            repo = JsonRepository("books.json")
        elif config.STORAGE_TYPE == "jsonbin":
            repo = JsonBinRepository(config.JSONBIN_API_KEY, config.JSONBIN_BIN_ID)
        else:
            repo = InMemoryRepository()

        repo.api_client = api_client
        logger.info(f"Using {config.STORAGE_TYPE} storage")

    except RepositoryError as e:
        logger.error(f"Storage error: {str(e)}")
        repo = InMemoryRepository()
        repo.api_client = api_client
        logger.warning("Fallback to in-memory storage")

    app.state.repo = repo
    yield

    if hasattr(repo, 'close'):
        await repo.close()


app = FastAPI(lifespan=lifespan)


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


# Эндпоинты остаются без изменений
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
        author: Optional[str] = None
):
    """
    Получить список книг с возможностью фильтрации:

    - **genre**: Фильтрация по жанру
    - **available**: Фильтрация по доступности (true/false)
    - **author**: Фильтрация по автору (частичное совпадение)
    """
    repo = app.state.repo
    all_books = await repo.get_all_books()

    # Применяем фильтры
    if genre:
        all_books = [b for b in all_books if b.genre and genre.lower() in b.genre.lower()]

    if author:
        all_books = [b for b in all_books if b.author and author.lower() in b.author.lower()]

    if available is not None:
        all_books = [b for b in all_books if b.available == available]

    return all_books


@app.get("/books/{book_id}", response_model=Book, summary="Получить книгу по ID")
async def get_book(book_id: int):
    """Получить детальную информацию о конкретной книге по её идентификатору"""
    repo = app.state.repo
    book = await repo.get_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return book


@app.post("/books",
          response_model=Book,
          status_code=status.HTTP_201_CREATED,
          summary="Добавить новую книгу",
          description="Добавляет новую книгу в каталог. При указании ISBN автоматически дополняет данные из Open Library API.")
async def add_book(book: BookCreate):
    """
    Добавить новую книгу в каталог:

    При указании ISBN система автоматически попытается дополнить информацию:
    - Описание книги
    - URL обложки
    - Рейтинг

    Поля, заполненные пользователем, имеют приоритет над данными из Open Library.
    """
    repo = app.state.repo
    try:
        return await repo.add_book(book)
    except Exception as e:
        logger.error(f"Error adding book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при добавлении книги"
        )


@app.put("/books/{book_id}", response_model=Book, summary="Обновить информацию о книге")
async def update_book(book_id: int, book_update: BookCreate):
    """Обновить информацию о существующей книге"""
    repo = app.state.repo
    updated_book = await repo.update_book(book_id, book_update)
    if not updated_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return updated_book


@app.delete("/books/{book_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Удалить книгу из каталога")
async def delete_book(book_id: int):
    """Удалить книгу из каталога по её идентификатору"""
    repo = app.state.repo
    success = await repo.delete_book(book_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return
