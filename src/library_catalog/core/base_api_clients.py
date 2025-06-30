import httpx
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from .exceptions import ApiClientError

class BaseApiClient(ABC):
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                response = await client.request(
                    method,
                    url,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error {e.response.status_code}: {url}")
            raise ApiClientError(f"API returned {e.response.status_code}") from e
        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise ApiClientError("API request failed") from e

    @abstractmethod
    async def get_data(self, identifier: str) -> Dict[str, Any]:
        pass