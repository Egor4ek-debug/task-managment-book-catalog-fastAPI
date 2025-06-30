import asyncpg
from typing import List, Optional
from ..core.base_repository import BookRepositoryBase
from ..core.exceptions import RepositoryError, BookNotFoundError
from ..models.book import Book, BookCreate


class PostgresRepository(BookRepositoryBase):
    def __init__(self, dsn: str):
        super().__init__()
        self.dsn = dsn
        self.pool = None
        self.api_client = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=5,
                max_size=20
            )
            await self._create_tables()
        except Exception as e:
            raise RepositoryError(f"Connection failed: {str(e)}") from e

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
                    rating FLOAT,
                    isbn TEXT
                )
            ''')


    async def get_all_books(self) -> List[Book]:
        async with self.pool.acquire() as conn:
            records = await conn.fetch("SELECT * FROM books")
            return [Book(**dict(record)) for record in records]

    async def get_book_by_id(self, book_id: int) -> Optional[Book]:
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                "SELECT * FROM books WHERE id = $1", book_id
            )
            return Book(**dict(record)) if record else None

    async def add_book(self, book: BookCreate) -> Book:
        book = await self._enrich_book_data(book, self.api_client)
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                """
                INSERT INTO books (
                    title, author, year, genre, pages, available, 
                    description, cover_url, rating, isbn
                ) 
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING *
                """,
                book.title, book.author, book.year, book.genre, book.pages,
                book.available, book.description, book.cover_url,
                book.rating, book.isbn
            )
            return Book(**dict(record))

    async def update_book(self, book_id: int, book_update: BookCreate) -> Optional[Book]:
        book = await self._enrich_book_data(book_update, self.api_client)
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                """
                UPDATE books SET
                    title = $1,
                    author = $2,
                    year = $3,
                    genre = $4,
                    pages = $5,
                    available = $6,
                    description = $7,
                    cover_url = $8,
                    rating = $9,
                    isbn = $10
                WHERE id = $11
                RETURNING *
                """,
                book.title, book.author, book.year, book.genre, book.pages,
                book.available, book.description, book.cover_url,
                book.rating, book.isbn, book_id
            )
            return Book(**dict(record)) if record else None

    async def delete_book(self, book_id: int) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM books WHERE id = $1", book_id
            )
            return result.split()[1] == '1'

    async def close(self):
        if self.pool:
            await self.pool.close()