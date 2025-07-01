class RepositoryError(Exception):
    """Base exception for repository operations"""


class ApiClientError(Exception):
    """Base exception for API client errors"""


class BookNotFoundError(RepositoryError):
    """Book not found in repository"""


class StorageConnectionError(RepositoryError):
    """Error connecting to storage"""
