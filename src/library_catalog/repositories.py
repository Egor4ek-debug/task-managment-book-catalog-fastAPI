import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from .models import Book, BookCreate


class BookRepository:
    def __init__(self, file_path: str = "books.json"):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Создает файл, если он не существует"""
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def _read_books(self) -> List[Dict]:
        """Читает все книги из файла"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_books(self, books: List[Dict]) -> None:
        """Записывает книги в файл"""
        temp_path = self.file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(books, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, self.file_path)

    def get_all_books(self) -> List[Book]:
        """Возвращает все книги"""
        books_data = self._read_books()
        return [Book.model_validate(book) for book in books_data]

    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """Находит книгу по ID"""
        books_data = self._read_books()
        for book in books_data:
            if book["id"] == book_id:
                return Book.model_validate(book)
        return None

    def add_book(self, book: BookCreate) -> Book:
        """Добавляет новую книгу"""
        books_data = self._read_books()

        # Генерируем новый ID
        new_id = max((b["id"] for b in books_data), default=0) + 1

        # Создаем словарь для новой книги
        new_book_dict = {
            "id": new_id,
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "genre": book.genre,
            "pages": book.pages,
            "available": book.available
        }

        books_data.append(new_book_dict)
        self._write_books(books_data)
        return Book.model_validate(new_book_dict)

    def update_book(self, book_id: int, book_update: BookCreate) -> Optional[Book]:
        """Обновляет информацию о книге"""
        books_data = self._read_books()
        updated_book = None

        for book in books_data:
            if book["id"] == book_id:
                # Обновляем поля книги
                book.update({
                    "title": book_update.title,
                    "author": book_update.author,
                    "year": book_update.year,
                    "genre": book_update.genre,
                    "pages": book_update.pages,
                    "available": book_update.available
                })
                updated_book = book
                break

        if updated_book:
            self._write_books(books_data)
            return Book.model_validate(updated_book)
        return None

    def delete_book(self, book_id: int) -> bool:
        """Удаляет книгу"""
        books_data = self._read_books()
        initial_count = len(books_data)

        books_data = [b for b in books_data if b["id"] != book_id]

        if len(books_data) < initial_count:
            self._write_books(books_data)
            return True
        return False