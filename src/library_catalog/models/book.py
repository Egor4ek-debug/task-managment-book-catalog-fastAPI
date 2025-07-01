from typing import Optional

from pydantic import BaseModel, Field


class BookBase(BaseModel):
    title: str
    author: str
    year: int = Field(..., gt=0)
    genre: str
    pages: int = Field(..., gt=0)
    available: bool = True
    description: Optional[str] = None
    cover_url: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    isbn: Optional[str] = None

    class Config:
        orm_mode = True


class BookCreate(BookBase):
    pass


class Book(BookBase):
    id: int
