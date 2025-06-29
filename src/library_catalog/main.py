from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from typing import List, Optional
from .models import Book, BookCreate
# from .repositories import BookRepository
from .postgres_repository import BookRepositoryPostgres
import os
from dotenv import load_dotenv

config = load_dotenv()
print(os.getenv("DATABASE_URL"))

DATABASE_URL = os.getenv("DATABASE_URL")

# # Создаем экземпляр репозитория
# book_repo = BookRepository("library_books.json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске приложения"""
    repo = BookRepositoryPostgres(DATABASE_URL)
    await repo.connect()
    app.state.repo = repo
    yield
    await repo.close()


app = FastAPI(
    title="Library Catalog API",
    description="Управление книжным каталогом библиотеки",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в систему управления библиотекой!"}


@app.get("/books", response_model=List[Book])
async def get_books(
        genre: Optional[str] = None,
        available: Optional[bool] = None
):
    """Получить список книг с фильтрацией"""
    repo = app.state.repo
    all_books = await repo.get_all_books()

    if genre:
        all_books = [b for b in all_books if b.genre.lower() == genre.lower()]

    if available is not None:
        all_books = [b for b in all_books if b.available == available]

    return all_books


@app.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: int):
    """Получить информацию о конкретной книге"""
    repo = app.state.repo
    book = await repo.get_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return book


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
async def add_book(book: BookCreate):
    """Добавить новую книгу в каталог"""
    repo = app.state.repo
    return await repo.add_book(book)


@app.put("/books/{book_id}", response_model=Book)
async def update_book(book_id: int, book_update: BookCreate):
    """Обновить информацию о книге"""
    repo = app.state.repo
    updated_book = await repo.update_book(book_id, book_update)
    if not updated_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return updated_book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int):
    """Удалить книгу из каталога"""
    repo = app.state.repo
    if not await repo.delete_book(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return