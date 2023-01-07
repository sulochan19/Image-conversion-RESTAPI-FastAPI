from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base


class Conversion(Base):
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String)
    png_url = Column(String)
    status = Column(String)
    created_at = Column(DateTime)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)

