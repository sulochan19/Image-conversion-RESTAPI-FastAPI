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
