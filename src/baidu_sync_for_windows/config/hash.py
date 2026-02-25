from pydantic_settings import SettingsConfigDict
from .base import TomlBaseSettings
from pydantic import Field, field_validator

class HashSettings(TomlBaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        pyproject_toml_table_header=("hash_settings",),
        extra="ignore",
    )
    algorithm: list[str] = Field(
        default=["md5", "sha1", "sha256"], description="哈希算法"
    )
    folder_fast_hash_algorithm: str = Field(
        default="sha256", description="文件夹快速hash算法"
    )
    folder_overcount: int = Field(
        default=100, description="文件夹下文件数量超过此值时，使用快速hash算法"
    )
    oversize: int = Field(
        default=20 * 1024 * 1024 * 1024,
        description="文件或者文件夹大小超过此值时，不再计算hash，由人工处理,默认20GB",
    )
    hash_chunk_size: int = Field(
        default=200 * 1024 * 1024, description="哈希单次读入大小,默认200MB"
    )
    fast_hash_chunk_size: int = Field(
        default=1 * 1024 * 1024, description="快速哈希单次读入大小,默认1MB"
    )
    max_workers: int = Field(
        default=4, description="哈希最大并发数,默认4", ge=1
    )

    @field_validator("oversize", mode="before")
    @classmethod
    def validate_algorithm(cls, v: int | str) -> int:
        if isinstance(v, str):
            return eval(v, {"__builtins__": None}, {})
        return v

    @field_validator("hash_chunk_size", mode="before")
    @classmethod
    def validate_hash_chunk_size(cls, v: int | str) -> int:
        if isinstance(v, str):
            return eval(v, {"__builtins__": None}, {})
        return v

    @field_validator("fast_hash_chunk_size", mode="before")
    @classmethod
    def validate_fast_hash_chunk_size(cls, v: int | str) -> int:
        if isinstance(v, str):
            return eval(v, {"__builtins__": None}, {})
        return v