import json
from pathlib import Path
from typing import List, Optional
from ..core.base_repository import BookRepositoryBase
from ..core.exceptions import RepositoryError
from ..models.book import Book, BookCreate


class JsonRepository(BookRepositoryBase):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = Path(file_path)
        self.api_client = None
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    async def _read_data(self) -> list:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RepositoryError(f"Error reading data: {str(e)}")

    async def _write_data(self, data: list):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RepositoryError(f"Error writing data: {str(e)}")

    async def get_all_books(self) -> List[Book]:
        data = await self._read_data()
        return [Book(**item) for item in data]


    async def get_book_by_id(self, book_id: int) -> Optional[Book]:
        data = await self._read_data()
        for item in data:
            if item["id"] == book_id:
                return Book(**item)
        return None

    async def add_book(self, book: BookCreate) -> Book:
        book = await self._enrich_book_data(book, self.api_client)
        data = await self._read_data()
        new_id = max(item["id"] for item in data) + 1 if data else 1
        new_book = Book(id=new_id, **book.dict())
        data.append(new_book.dict())
        await self._write_data(data)
        return new_book

    async def update_book(self, book_id: int, book_update: BookCreate) -> Optional[Book]:
        data = await self._read_data()
        for i, item in enumerate(data):
            if item["id"] == book_id:
                book = await self._enrich_book_data(book_update, self.api_client)
                # Сохраняем ID и обновляем остальные поля
                updated = {**item, **book.dict(), "id": book_id}
                data[i] = updated
                await self._write_data(data)
                return Book(**updated)
        return None

    async def delete_book(self, book_id: int) -> bool:
        data = await self._read_data()
        initial_length = len(data)
        data = [item for item in data if item["id"] != book_id]
        if len(data) < initial_length:
            await self._write_data(data)
            return True
        return False