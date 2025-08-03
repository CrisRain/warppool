from sqlalchemy import Boolean, Column, Integer, String
from .database import Base

class WarpInstance(Base):
    __tablename__ = "warp_instances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    socks5_port = Column(Integer, unique=True, nullable=False)
    is_managed = Column(Boolean, default=True)