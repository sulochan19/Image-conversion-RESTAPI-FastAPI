from pydantic import BaseModel
from datetime import datetime

class Conversion(BaseModel):
    id:int
    source_file: str
    png_url: str
    status: str
    created_at: datetime
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str

    class config:
        orm_mode = True
