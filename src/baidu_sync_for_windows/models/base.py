from sqlalchemy.orm import  Mapped, mapped_column,MappedAsDataclass,DeclarativeBase
from sqlalchemy import Integer,BigInteger
from datetime import datetime
from time import time_ns
from typing import Optional

class Base(MappedAsDataclass,DeclarativeBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True,init=False)
    created_at: Mapped[int] = mapped_column(BigInteger, default=time_ns,init=False)
    updated_at: Mapped[int] = mapped_column(BigInteger, onupdate=time_ns,nullable=True,init=False)
    latested_at: Mapped[int] = mapped_column(BigInteger, default=time_ns,onupdate=time_ns,init=False)

    @property
    def created_time_to_local_time(self) -> Optional[datetime]:
        if self.created_at is None:
            return None
        return datetime.fromtimestamp(self.created_at / 1_000_000_000)
    @property
    def updated_time_to_local_time(self) -> Optional[datetime]:
        if self.updated_at is None:
            return None
        return datetime.fromtimestamp(self.updated_at / 1_000_000_000)
    @property
    def latested_time_to_local_time(self) -> Optional[datetime]:
        if self.latested_at is None:
            return None
        return datetime.fromtimestamp(self.latested_at / 1_000_000_000)
    