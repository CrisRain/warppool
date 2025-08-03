from pydantic import BaseModel
from typing import Optional

class WarpInstanceBase(BaseModel):
    name: str
    socks5_port: int
    is_managed: bool = True

class WarpInstanceCreate(WarpInstanceBase):
    pass

class WarpInstanceUpdate(BaseModel):
    name: Optional[str] = None
    socks5_port: Optional[int] = None
    is_managed: Optional[bool] = None

class WarpInstance(WarpInstanceBase):
    id: int

    class Config:
        orm_mode = True