from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BookModel(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    genre = Column(String, nullable=False)
    pages = Column(Integer, nullable=False)
    available = Column(Boolean, default=True)
    description = Column(String)
    cover_url = Column(String)
    rating = Column(Float)
    isbn = Column(String)
