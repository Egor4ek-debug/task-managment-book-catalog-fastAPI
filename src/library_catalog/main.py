from typing import List, Optional

from fastapi import FastAPI, HTTPException
from starlette import status

from .models import Book, BookCreate

app = FastAPI(
    title="Library Catalog API",
    description="Управление книжным каталогом библиотеки",
    version="0.1.0",
)

books_db = [
    {
        "id": 1,
        "title": "Война и мир",
        "author": "Лев Толстой",
        "year": 1869,
        "genre": "Роман",
        "pages": 1225,
        "available": True
    },
    {
        "id": 2,
        "title": "Преступление и наказание",
        "author": "Федор Достоевский",
        "year": 1866,
        "genre": "Роман",
        "pages": 672,
        "available": True
    },
    {
        "id": 3,
        "title": "1984",
        "author": "Джордж Оруэлл",
        "year": 1949,
        "genre": "Антиутопия",
        "pages": 328,
        "available": False
    },
    {
        "id": 4,
        "title": "Мастер и Маргарита",
        "author": "Михаил Булгаков",
        "year": 1967,
        "genre": "Роман",
        "pages": 480,
        "available": True
    },
    {
        "id": 5,
        "title": "Гарри Поттер и философский камень",
        "author": "Джоан Роулинг",
        "year": 1997,
        "genre": "Фэнтези",
        "pages": 432,
        "available": True
    }
]
current_len = len(books_db) + 1


@app.get("/")
def main_page():
    return 'Добро пожаловать в книжный каталог!'


@app.get('/books', response_model=List[Book])
def get_books(genre: Optional[str] = None, available: Optional[bool] = None):
    """Получить список книг с фильтрацией по жанру и доступности"""
    filtered_books = books_db

    if genre:
        filtered_books = [b for b in filtered_books if b.genre.lower() == genre.lower()]

    if available:
        filtered_books = [b for b in filtered_books if b.available == available]

    return filtered_books


@app.get('/books/{book_id}', response_model=Book)
def get_book(book_id: int):
    """Получить информацию о конкретной книге"""

    book = next((b for b in books_db if b['id'] == book_id), None)

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return book


@app.post('/books', response_model=Book, status_code=status.HTTP_201_CREATED)
def add_book(book: BookCreate):
    """Добавить новую книгу в каталог"""

    global current_len
    new_book = Book(
        id=current_len,
        **book.__dict__
    )
    books_db.append(new_book)
    current_len += 1
    return new_book


@app.put('/books/{book_id}', response_model=Book)
def update_book(book_id: int, book_update: BookCreate):
    """Обновить информацию о книге"""
    book_index = next((i for i, b in enumerate(books_db) if b['id'] == book_id), None)

    if book_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )

    updated_book = Book(
        id=book_id,
        **book_update.__dict__
    )
    books_db[book_index] = updated_book
    return updated_book


@app.delete('/books/{book_id}',status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id:int):
    global books_db
    initial_length = len(books_db)

    books_db = [b for b in books_db if b['id'] != book_id]

    if len(books_db) == initial_length:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )