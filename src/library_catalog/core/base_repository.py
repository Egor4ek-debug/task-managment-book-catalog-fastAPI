import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.book import Book, BookCreate


class BookRepositoryBase(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def get_all_books(self) -> List[Book]:
        pass

    @abstractmethod
    async def get_book_by_id(self, book_id: int) -> Optional[Book]:
        pass

    @abstractmethod
    async def add_book(self, book: BookCreate, skip_enrichment: bool = False) -> Book:
        pass

    @abstractmethod
    async def update_book(self, book_id: int, book_update: BookCreate, skip_enrichment: bool = False) -> Optional[Book]:
        pass

    @abstractmethod
    async def delete_book(self, book_id: int) -> bool:
        pass

    async def _enrich_book_data(self, book: BookCreate, api_client) -> BookCreate:
        if not api_client or not book.isbn:
            return book

        try:
            data = await api_client.get_data(book.isbn)
            if not book.description and data.get("description"):
                book.description = data["description"]
            if not book.cover_url and data.get("cover_url"):
                book.cover_url = data["cover_url"]
            if book.rating is None and data.get("rating") is not None:
                book.rating = data["rating"]
        except Exception as e:
            self.logger.error(f"Enrichment failed: {str(e)}")
        return book
