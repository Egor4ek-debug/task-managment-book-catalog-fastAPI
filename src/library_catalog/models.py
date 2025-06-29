from pydantic import BaseModel, Field
from typing import Optional


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


class BookCreate(BookBase):
    isbn: Optional[str] = None


class Book(BookBase):
    id: int

    class Config:
        orm_mode = True