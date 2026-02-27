from sqlalchemy import create_engine,Engine
from sqlalchemy.orm import Session
from typing import Any
from .models import CacheRecord


class CacheService:
    def __init__(self, engine: Engine|None = None):
        self.engine = engine or self._default_engine()
        self.create_cache_table()
    def _default_engine(self)->Engine:
        return create_engine(
            "sqlite:///:memory:"
        )
    def get_session(self)->Session:
        return Session(self.engine)
    def get_cache_record(self, service_tag: str, cache_key: str)->Any|None:
        with self.get_session() as session:
            record = session.query(CacheRecord).filter(CacheRecord.service_tag == service_tag, CacheRecord.cache_key == cache_key).first()
            return record.cache_value if record else None
    def set_cache_record(self, service_tag: str, cache_key: str, cache_value: Any):
        with self.get_session() as session:
            session.add(CacheRecord(service_tag=service_tag, cache_key=cache_key, cache_value=cache_value))
            session.commit()
    def clear_cache_record(self, service_tag: str):
        with self.get_session() as session:
            session.query(CacheRecord).filter(CacheRecord.service_tag == service_tag).delete()
            session.commit()
    def clear_all_cache_record(self):
        with self.get_session() as session:
            session.query(CacheRecord).delete()
            session.commit()
    def reset_cache_record(self):
        CacheRecord.metadata.drop_all(self.engine)
        CacheRecord.metadata.create_all(self.engine)
    def create_cache_table(self)->None:
        CacheRecord.metadata.create_all(self.engine)