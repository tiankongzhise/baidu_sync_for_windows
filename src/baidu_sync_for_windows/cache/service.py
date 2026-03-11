from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from typing import Any, overload
from .models import CacheRecord


class CacheService:
    def __init__(self, engine: Engine | None = None, service_tag: str | None = None,is_memory: bool = True):
        self.engine = engine or self._default_engine(is_memory)
        self.service_tag = service_tag
        self.create_cache_table()

    def _default_engine(self,is_memory: bool = True) -> Engine:
        # 使用标准 :memory: 避免在 Windows 上被解析为文件路径导致 unable to open database file
        if is_memory:
            return create_engine("sqlite:///:memory:?cache=shared")
        else:
            return create_engine("sqlite:///cache.db?cache=shared")

    def get_session(self) -> Session:
        return Session(self.engine)

    @overload
    def get_cache_record(self, cache_key: str) -> Any | None: ...
    @overload
    def get_cache_record(self, service_tag: str, cache_key: str) -> Any | None: ...

    def get_cache_record(self, *args, **kwargs) -> Any | None:
        # 初始化参数
        service_tag: str = None  # type: ignore
        cache_key: str = None  # type: ignore

        if len(args) + len(kwargs) > 2:
            raise ValueError(
                f"Too many arguments, only one of cache_key or service_tag and cache_key is allowed, got {args} and {kwargs}"
            )
        match args:
            case [cache_key]:
                cache_key = cache_key
            case [service_tag, cache_key]:
                service_tag = service_tag
                cache_key = cache_key
            case _:
                raise ValueError(
                    f"Too many arguments, only one of cache_key or service_tag and cache_key is allowed, got {args}"
                )
        if kwargs:
            if "service_tag" in kwargs:
                service_tag = kwargs["service_tag"]
            if "cache_key" in kwargs:
                cache_key = kwargs["cache_key"]
        if service_tag is None:
            service_tag = self.service_tag  # type: ignore
        if not all([service_tag, cache_key]):
            raise ValueError(
                f"service_tag and cache_key are required, got service_tag: {service_tag} and cache_key: {cache_key}"
            )
        with self.get_session() as session:
            record = (
                session.query(CacheRecord)
                .filter(
                    CacheRecord.service_tag == service_tag,
                    CacheRecord.cache_key == cache_key,
                )
                .first()
            )
            return record.cache_value if record else None

    @overload
    def set_cache_record(self, cache_key: str, cache_value: Any) -> None: ...
    @overload
    def set_cache_record(
        self, service_tag: str, cache_key: str, cache_value: Any
    ) -> None: ...
    def set_cache_record(self, *args, **kwargs) -> None:
        # 初始化参数
        service_tag: str = None  # type: ignore
        cache_key: str = None  # type: ignore
        cache_value: Any = None  # type: ignore

        if len(args) + len(kwargs) > 3:
            raise ValueError(
                f"Too many arguments, only one of cache_key, service_tag and cache_key is allowed, got {args} and {kwargs}"
            )
        match args:
            case [cache_key, cache_value]:
                cache_key = cache_key
                cache_value = cache_value
            case [service_tag, cache_key, cache_value]:
                service_tag = service_tag
                cache_key = cache_key
                cache_value = cache_value
            case _:
                raise ValueError(
                    f"Too many arguments, only one of cache_key or service_tag and cache_key is allowed, got {args}"
                )
        if kwargs:
            if "service_tag" in kwargs:
                service_tag = kwargs["service_tag"]
            if "cache_key" in kwargs:
                cache_key = kwargs["cache_key"]
            if "cache_value" in kwargs:
                cache_value = kwargs["cache_value"]
        if service_tag is None:
            service_tag = self.service_tag  # type: ignore
        if not all([service_tag, cache_key, cache_value]):
            raise ValueError(
                f"service_tag, cache_key and cache_value are required, got service_tag: {service_tag}, cache_key: {cache_key} and cache_value: {cache_value}"
            )
        with self.get_session() as session:
            session.add(
                CacheRecord(
                    service_tag=service_tag,
                    cache_key=cache_key,
                    cache_value=cache_value,
                )
            )
            session.commit()

    @overload
    def clear_cache_record(self, service_tag: str) -> None: ...
    @overload
    def clear_cache_record(self) -> None: ...
    def clear_cache_record(self, *args, **kwargs) -> None:
        # 初始化参数
        service_tag: str = None  # type: ignore
        if len(args) + len(kwargs) > 1:
            raise ValueError(
                f"Too many arguments, only one of service_tag is allowed, got {args} and {kwargs}"
            )
        match args:
            case [service_tag]:
                service_tag = service_tag
            case _:
                raise ValueError(
                    f"Too many arguments, only one of service_tag is allowed, got {args}"
                )
        if kwargs:
            if "service_tag" in kwargs:
                service_tag = kwargs["service_tag"]
        if service_tag is None:
            service_tag = self.service_tag  # type: ignore
        if not all([service_tag]):
            raise ValueError(f"service_tag is required, got service_tag: {service_tag}")
        with self.get_session() as session:
            session.query(CacheRecord).filter(
                CacheRecord.service_tag == service_tag
            ).delete()
            session.commit()

    def clear_all_cache_record(self):
        with self.get_session() as session:
            session.query(CacheRecord).delete()
            session.commit()

    def reset_cache_record(self):
        CacheRecord.metadata.drop_all(self.engine)
        CacheRecord.metadata.create_all(self.engine)

    def create_cache_table(self) -> None:
        CacheRecord.metadata.create_all(self.engine)
