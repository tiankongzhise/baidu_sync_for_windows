from pydantic_settings import SettingsConfigDict
from .base import TomlBaseSettings
from pydantic import Field
class VerifierSettings(TomlBaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        pyproject_toml_table_header=("verifier_settings",),
        extra="ignore",
    )
    uncompress_temp_dir: str = Field(
        default="D:\\backup_extract", description="解压临时目录"
    )
    uncompress_password: str = Field(default="H_x123456789", description="解压密码")