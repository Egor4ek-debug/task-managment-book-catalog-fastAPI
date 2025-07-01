from typing import List, Optional

from ..core.base_repository import BookRepositoryBase
from ..core.exceptions import RepositoryError, ApiClientError
from ..core.logging import setup_logging
from ..models.book import Book, BookCreate

logger = setup_logging()


class BookService:
    def __init__(self, repository: BookRepositoryBase):
        # Убедимся, что передаётся экземпляр репозитория, а не генератор
        if not isinstance(repository, BookRepositoryBase):
            raise TypeError("Repository must be an instance of BookRepositoryBase")

        self.repository = repository

    async def get_all_books(
            self,
            genre: Optional[str] = None,
            available: Optional[bool] = None,
            author: Optional[str] = None
    ) -> List[Book]:
        """Получить все книги с возможностью фильтрации"""
        try:
            books = await self.repository.get_all_books()

            # Применяем фильтры
            if genre:
                books = [b for b in books if b.genre and genre.lower() in b.genre.lower()]
            if author:
                books = [b for b in books if b.author and author.lower() in b.author.lower()]
            if available is not None:
                books = [b for b in books if b.available == available]

            return books
        except Exception as e:
            logger.error(f"Unexpected error in get_all_books: {str(e)}")
            raise RepositoryError("Error retrieving books") from e

    async def get_book_by_id(self, book_id: int) -> Book:
        """Получить книгу по ID"""
        try:
            book = await self.repository.get_book_by_id(book_id)
            if not book:
                raise RepositoryError(f"Book with ID {book_id} not found")
            return book
        except RepositoryError as e:
            logger.error(f"Repository error in get_book_by_id: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_book_by_id: {str(e)}")
            raise RepositoryError("Error retrieving book") from e

    async def add_book(self, book_data: BookCreate) -> Book:
        """Добавить новую книгу"""
        try:
            return await self.repository.add_book(book_data)
        except ApiClientError as e:
            logger.error(f"API client error in add_book: {str(e)}")
            # Пробуем добавить без обогащения данных
            logger.warning("Adding book without enrichment from external API")
            return await self.repository.add_book(book_data, skip_enrichment=True)
        except RepositoryError as e:
            logger.error(f"Repository error in add_book: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in add_book: {str(e)}")
            raise RepositoryError("Error adding book") from e

    async def update_book(self, book_id: int, book_data: BookCreate) -> Book:
        """Обновить информацию о книге"""
        try:
            updated_book = await self.repository.update_book(book_id, book_data)
            if not updated_book:
                raise RepositoryError(f"Book with ID {book_id} not found")
            return updated_book
        except ApiClientError as e:
            logger.error(f"API client error in update_book: {str(e)}")
            # Пробуем обновить без обогащения данных
            logger.warning("Updating book without enrichment from external API")
            return await self.repository.update_book(book_id, book_data, skip_enrichment=True)
        except RepositoryError as e:
            logger.error(f"Repository error in update_book: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in update_book: {str(e)}")
            raise RepositoryError("Error updating book") from e

    async def delete_book(self, book_id: int) -> bool:
        """Удалить книгу"""
        try:
            success = await self.repository.delete_book(book_id)
            if not success:
                raise RepositoryError(f"Book with ID {book_id} not found")
            return True
        except RepositoryError as e:
            logger.error(f"Repository error in delete_book: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in delete_book: {str(e)}")
            raise RepositoryError("Error deleting book") from e

    async def backup_books(self, backup_repository: BookRepositoryBase) -> bool:
        """Создать резервную копию книг"""
        try:
            books = await self.repository.get_all_books()
            for book in books:
                # Конвертируем Book в BookCreate (исключаем id)
                book_data = BookCreate(
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
                await backup_repository.add_book(book_data, skip_enrichment=True)
            return True
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return False
