from .base import TomlBaseSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict
class SourcePathSettings(TomlBaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        pyproject_toml_table_header=("source_path_settings",),
        extra="ignore",
    )
    target_path: list[str] = Field(default=[], description="目标路径")