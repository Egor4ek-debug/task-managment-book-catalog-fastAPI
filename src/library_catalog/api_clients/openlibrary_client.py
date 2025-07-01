from typing import Dict, Any

from ..api_clients.base_api_clients import BaseApiClient


class OpenLibraryClient(BaseApiClient):
    BASE_URL = "https://openlibrary.org"

    def __init__(self):
        super().__init__(self.BASE_URL)

    async def get_data(self, isbn: str) -> Dict[str, Any]:
        book_data = await self._request("GET", f"/isbn/{isbn}.json")
        work_id = self._extract_work_id(book_data)

        work_data = {}
        if work_id:
            try:
                work_data = await self._request("GET", f"/works/{work_id}.json")
            except Exception:
                pass

        return {
            "cover_url": self._get_cover_url(book_data),
            "description": self._extract_description(work_data or book_data),
            "rating": work_data.get("ratings_average")
        }

    def _extract_work_id(self, book_data: Dict) -> str:
        works = book_data.get("works", [])
        # Добавлена проверка на пустой список
        return works[0]["key"].split("/")[-1] if works and len(works) > 0 else None

    def _extract_description(self, data: Dict) -> str:
        description = data.get("description")
        if isinstance(description, str):
            return description
        if isinstance(description, dict):
            return description.get("value")
        return None

    def _get_cover_url(self, book_data: Dict) -> str:
        covers = book_data.get("covers", [])
        return f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg" if covers else None
