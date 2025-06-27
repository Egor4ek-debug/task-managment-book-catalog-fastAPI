from pydantic import BaseModel

class BookBase(BaseModel):
    title: str
    author: str
    year: int
    genre: str
    pages: int
    available: bool = True

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    class Config:
        orm_mode = True

