from typing import List, Optional
from ..core.base_repository import BookRepositoryBase
from ..models.book import Book, BookCreate


class InMemoryRepository(BookRepositoryBase):
    def __init__(self):
        super().__init__()
        self.books = []
        self.next_id = 1
        self.api_client = None

    async def get_all_books(self) -> List[Book]:
        return self.books.copy()

    async def get_book_by_id(self, book_id: int) -> Optional[Book]:
        return next((b for b in self.books if b.id == book_id), None)

    async def add_book(self, book: BookCreate) -> Book:
        book = await self._enrich_book_data(book, self.api_client)
        new_book = Book(
            id=self.next_id,
            **book.dict()
        )
        self.books.append(new_book)
        self.next_id += 1
        return new_book


    async def update_book(self, book_id: int, book_update: BookCreate) -> Optional[Book]:
        for i, b in enumerate(self.books):
            if b.id == book_id:
                updated_book = await self._enrich_book_data(book_update, self.api_client)
                # Сохраняем неизменяемые поля
                updated_data = {**b.dict(), **updated_book.dict()}
                updated_data["id"] = book_id
                self.books[i] = Book(**updated_data)
                return self.books[i]
        return None

    async def delete_book(self, book_id: int) -> bool:
        initial_count = len(self.books)
        self.books = [b for b in self.books if b.id != book_id]
        return len(self.books) < initial_count
