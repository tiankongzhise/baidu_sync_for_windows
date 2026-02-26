from pydantic_settings import SettingsConfigDict
from .base import TomlBaseSettings
from pydantic import Field
class LoggingSettings(TomlBaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        pyproject_toml_table_header=("loguru_settings",),
        extra="ignore",
    )
    console_level: str = Field(default="SERVICE_INFO", description="日志级别")