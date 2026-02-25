
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
)

import platform
from typing import Type, Tuple
from pathlib import Path


def drive_letter():
    return f"{platform.node()}|{platform.processor()}".upper()


class EnvBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
class TomlBaseSettings(BaseSettings):
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        # 返回您想要使用的源，按优先级排序
        # TOML 文件 (config.toml) > 环境变量 > .env 文件 > init 参数
        # 使用 PyprojectTomlConfigSettingsSource 并指定 toml_file 以支持 pyproject_toml_table_header
        return (
            init_settings,
            env_settings,
            PyprojectTomlConfigSettingsSource(
                settings_cls, toml_file=Path("config.toml")
            ),
            dotenv_settings,
            file_secret_settings,
        )