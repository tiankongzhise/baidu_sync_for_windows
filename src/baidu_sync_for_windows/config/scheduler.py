from pydantic_settings import SettingsConfigDict
from .base import TomlBaseSettings
from pydantic import Field
class SchedulerSettings(TomlBaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        pyproject_toml_table_header=("scheduler_settings",),
        extra="ignore",
    )
    quotas: dict[str, int] = Field(
        default={
            "compress": 40 * 1024 * 1024 * 1024, # 40GB
            "verify": 40 * 1024 * 1024 * 1024, # 40GB
        },
        description="资源配额",
    )