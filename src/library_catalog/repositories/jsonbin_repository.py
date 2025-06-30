import json
import logging
from typing import List, Optional
from httpx import AsyncClient
from ..core.base_repository import BookRepositoryBase
from ..core.exceptions import RepositoryError
from ..models.book import Book, BookCreate

class JsonBinRepository(BookRepositoryBase):
    BASE_URL = "https://api.jsonbin.io/v3/b"

    def __init__(self, api_key: str, bin_id: str):
        super().__init__()
        self.api_key = api_key
        self.bin_id = bin_id
        self.api_client = None
        self.headers = {
            "Content-Type": "application/json",
            "X-Master-Key": api_key,
            "X-Bin-Meta": "false"
        }

    async def _fetch_data(self) -> list:
        async with AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{self.bin_id}/latest",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def _update_data(self, data: list):
        async with AsyncClient() as client:
            response = await client.put(
                f"{self.BASE_URL}/{self.bin_id}",
                headers=self.headers,
                content=json.dumps(data))
            response.raise_for_status()

    async def get_all_books(self) -> List[Book]:
        try:
            data = await self._fetch_data()
            return [Book(**item) for item in data]
        except Exception as e:
            self.logger.error(f"JSONBin read error: {str(e)}")
            raise RepositoryError("Error reading from JSONBin")

    async def get_book_by_id(self, book_id: int) -> Optional[Book]:
        data = await self._fetch_data()
        for item in data:
            if item["id"] == book_id:
                return Book(**item)
        return None

    async def add_book(self, book: BookCreate) -> Book:
        book = await self._enrich_book_data(book, self.api_client)
        data = await self._fetch_data()
        new_id = max(item["id"] for item in data) + 1 if data else 1
        new_book = Book(id=new_id, **book.dict())
        data.append(new_book.dict())
        await self._update_data(data)
        return new_book

    async def update_book(self, book_id: int, book_update: BookCreate) -> Optional[Book]:
        data = await self._fetch_data()
        for i, item in enumerate(data):
            if item["id"] == book_id:
                book = await self._enrich_book_data(book_update, self.api_client)
                updated = {**item, **book.dict(), "id": book_id}
                data[i] = updated
                await self._update_data(data)
                return Book(**updated)
        return None

    async def delete_book(self, book_id: int) -> bool:
        data = await self._fetch_data()
        initial_length = len(data)
        data = [item for item in data if item["id"] != book_id]
        if len(data) < initial_length:
            await self._update_data(data)
            return True
        return False