from typing import List, Optional

import asyncpg
from .models import Book, BookCreate

class BookRepositoryPostgres():
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=5,
            max_size=20
        )
        await self._create_tables()

    async def _create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    genre TEXT NOT NULL,
                    pages INTEGER NOT NULL,
                    available BOOLEAN NOT NULL DEFAULT TRUE,
                    description TEXT,
                    cover_url TEXT,
                    rating FLOAT
                )
            ''')

    async def get_all_books(self) -> List[Book]:
        """Возвращает все книги"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM books")
            return [Book(**row) for row in rows]

    async def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """Находит книгу по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM books WHERE id = $1",
                book_id
            )
            return Book(**row) if row else None

    async def add_book(self, book: BookCreate) -> Book:
        """Добавляет новую книгу"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO books (title, author, year, genre, pages, available)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                book.title, book.author, book.year,
                book.genre, book.pages, book.available
            )
            return Book(**row)

    async def update_book(self, book_id: int, book_update: BookCreate) -> Optional[Book]:
        """Обновляет информацию о книге"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE books
                SET title = $1, author = $2, year = $3, 
                    genre = $4, pages = $5, available = $6
                WHERE id = $7
                RETURNING *
                """,
                book_update.title, book_update.author, book_update.year,
                book_update.genre, book_update.pages, book_update.available,
                book_id
            )
            return Book(**row) if row else None

    async def delete_book(self, book_id: int) -> bool:
        """Удаляет книгу"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM books WHERE id = $1",
                book_id
            )
            return "DELETE 1" in result

    async def close(self):
        """Закрывает пул подключений"""
        if self.pool:
            await self.pool.close()