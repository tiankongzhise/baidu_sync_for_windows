from pydantic_settings import SettingsConfigDict
from .base import TomlBaseSettings
from pydantic import Field, field_validator
class ScanSettings(TomlBaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        pyproject_toml_table_header=("scan_settings",),
        extra="ignore",
    )
    oversize: int = Field(
        default=20 * 1024 * 1024 * 1024,
        description="文件或者文件夹大小超过此值时，不再计算hash，由人工处理,默认20GB",
    )
    @field_validator("oversize", mode="before")
    @classmethod
    def validate_algorithm(cls, v: int | str) -> int:
        if isinstance(v, str):
            return eval(v, {"__builtins__": None}, {})
        return v