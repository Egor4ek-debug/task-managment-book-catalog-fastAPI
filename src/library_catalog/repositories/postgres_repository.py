import logging
from typing import List, Optional

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..core.base_repository import BookRepositoryBase
from ..core.exceptions import RepositoryError
from ..models.base import BookModel
from ..models.book import Book, BookCreate

logger = logging.getLogger(__name__)


class BaseSQLAlchemyRepository:
    """Базовый класс для репозиториев SQLAlchemy"""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.engine = None
        self.async_session = None

    async def connect(self):
        """Инициализация движка и сессии SQLAlchemy"""
        if self.engine is None:
            try:
                from sqlalchemy.ext.asyncio import create_async_engine
                from sqlalchemy.orm import sessionmaker

                self.engine = create_async_engine(
                    self.dsn,
                    echo=False,
                    future=True,
                    poolclass=None  # Используем пул по умолчанию
                )

                # Создаем асинхронную сессию
                self.async_session = sessionmaker(
                    self.engine, expire_on_commit=False, class_=AsyncSession
                )
                logger.info("SQLAlchemy connection initialized")
            except Exception as e:
                raise RepositoryError(f"Connection failed: {str(e)}") from e

    async def ensure_connected(self):
        """Гарантирует, что соединение инициализировано"""
        if self.engine is None:
            await self.connect()

    async def close(self):
        """Закрытие соединения"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.async_session = None
            logger.info("SQLAlchemy connection closed")


class PostgresRepository(BookRepositoryBase, BaseSQLAlchemyRepository):
    def __init__(self, dsn: str):
        BookRepositoryBase.__init__(self)
        BaseSQLAlchemyRepository.__init__(self, dsn)
        self.api_client = None

    async def _convert_to_pydantic(self, db_book: BookModel) -> Book:
        """Конвертирует модель SQLAlchemy в модель Pydantic"""
        return Book(
            id=db_book.id,
            title=db_book.title,
            author=db_book.author,
            year=db_book.year,
            genre=db_book.genre,
            pages=db_book.pages,
            available=db_book.available,
            description=db_book.description,
            cover_url=db_book.cover_url,
            rating=db_book.rating,
            isbn=db_book.isbn
        )

    async def get_all_books(self) -> List[Book]:
        await self.ensure_connected()
        async with self.async_session() as session:
            try:
                result = await session.execute(select(BookModel))
                books = []
                for db_book in result.scalars():
                    books.append(await self._convert_to_pydantic(db_book))
                return books
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error: {str(e)}")
                raise RepositoryError("Database error") from e

    async def get_book_by_id(self, book_id: int) -> Optional[Book]:
        await self.ensure_connected()
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    select(BookModel).where(BookModel.id == book_id))
                db_book = result.scalar_one_or_none()
                if db_book:
                    return await self._convert_to_pydantic(db_book)
                return None
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error: {str(e)}")
                raise RepositoryError("Database error") from e

    async def add_book(self, book: BookCreate, skip_enrichment: bool = False) -> Book:
        if not skip_enrichment and self.api_client:
            book = await self._enrich_book_data(book, self.api_client)

        await self.ensure_connected()
        async with self.async_session() as session:
            try:
                # Создаем экземпляр модели SQLAlchemy
                db_book = BookModel(
                    title=book.title,
                    author=book.author,
                    year=book.year,
                    genre=book.genre,
                    pages=book.pages,
                    available=book.available,
                    description=book.description,
                    cover_url=book.cover_url,
                    rating=book.rating,
                    isbn=book.isbn
                )

                session.add(db_book)
                await session.commit()
                await session.refresh(db_book)
                return await self._convert_to_pydantic(db_book)
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"SQLAlchemy error: {str(e)}")
                raise RepositoryError("Error adding book") from e

    async def update_book(self, book_id: int, book_update: BookCreate, skip_enrichment: bool = False) -> Optional[Book]:
        if not skip_enrichment and self.api_client:
            book_update = await self._enrich_book_data(book_update, self.api_client)

        await self.ensure_connected()
        async with self.async_session() as session:
            try:
                # Получаем книгу для обновления
                result = await session.execute(
                    select(BookModel).where(BookModel.id == book_id))
                db_book = result.scalar_one_or_none()

                if not db_book:
                    return None

                # Обновляем поля
                db_book.title = book_update.title
                db_book.author = book_update.author
                db_book.year = book_update.year
                db_book.genre = book_update.genre
                db_book.pages = book_update.pages
                db_book.available = book_update.available
                db_book.description = book_update.description
                db_book.cover_url = book_update.cover_url
                db_book.rating = book_update.rating
                db_book.isbn = book_update.isbn

                await session.commit()
                await session.refresh(db_book)
                return await self._convert_to_pydantic(db_book)
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"SQLAlchemy error: {str(e)}")
                raise RepositoryError("Error updating book") from e

    async def delete_book(self, book_id: int) -> bool:
        await self.ensure_connected()
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    delete(BookModel).where(BookModel.id == book_id))
                await session.commit()
                return result.rowcount > 0
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"SQLAlchemy error: {str(e)}")
                raise RepositoryError("Error deleting book") from e
