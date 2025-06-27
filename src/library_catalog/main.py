from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from typing import List, Optional
from .models import Book, BookCreate
from .repositories import BookRepository

# Создаем экземпляр репозитория
book_repo = BookRepository("library_books.json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске приложения"""
    # Создаем тестовые данные, если их нет
    if not book_repo.get_all_books():
        # Создаем объекты BookCreate для тестовых данных
        initial_books = [
            BookCreate(
                title="Война и мир",
                author="Лев Толстой",
                year=1869,
                genre="Роман",
                pages=1225,
                available=True
            ),
            BookCreate(
                title="Преступление и наказание",
                author="Федор Достоевский",
                year=1866,
                genre="Роман",
                pages=672,
                available=True
            ),
            BookCreate(
                title="1984",
                author="Джордж Оруэлл",
                year=1949,
                genre="Антиутопия",
                pages=328,
                available=False
            )
        ]

        # Добавляем книги через репозиторий
        for book in initial_books:
            book_repo.add_book(book)
    yield


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
def get_books(
        genre: Optional[str] = None,
        available: Optional[bool] = None
):
    """Получить список книг с фильтрацией"""
    all_books = book_repo.get_all_books()

    if genre:
        all_books = [b for b in all_books if b.genre.lower() == genre.lower()]

    if available is not None:
        all_books = [b for b in all_books if b.available == available]

    return all_books


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    """Получить информацию о конкретной книге"""
    book = book_repo.get_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return book


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def add_book(book: BookCreate):
    """Добавить новую книгу в каталог"""
    return book_repo.add_book(book)


@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book_update: BookCreate):
    """Обновить информацию о книге"""
    updated_book = book_repo.update_book(book_id, book_update)
    if not updated_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return updated_book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int):
    """Удалить книгу из каталога"""
    if not book_repo.delete_book(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return