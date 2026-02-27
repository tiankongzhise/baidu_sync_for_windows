
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import MetaData,String,JSON,UniqueConstraint,Integer

class CacheBase(DeclarativeBase):
    __abstract__ = True
    metadata = MetaData()

class CacheRecord(CacheBase):
    __tablename__ = "cache_record"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_tag: Mapped[str] = mapped_column(String(40))
    cache_key:Mapped[str] = mapped_column(String(40))
    cache_value:Mapped[dict] = mapped_column(JSON)

    __table_args__ = (
        UniqueConstraint(service_tag,cache_key,name="uix_service_tag_cache_key"),
    )