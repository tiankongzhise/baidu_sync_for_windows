from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict,BaseSettings
from .base import EnvBaseSettings,TomlBaseSettings
from typing import Literal

class DatabaseSecretInfo(EnvBaseSettings):
    # model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")
    db_host: SecretStr = Field(..., description="数据库主机")
    db_port: int = Field(default=3306, description="数据库端口", ge=1, le=65535)
    db_user: SecretStr = Field(..., description="数据库用户")
    db_password: SecretStr = Field(default="", description="数据库密码")
    db_name: SecretStr = Field(default="", description="数据库名称")
class DatabaseConfig(TomlBaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        pyproject_toml_table_header=("db_settings",),
        extra="ignore",
    )
    database: Literal["mysql", "posgresql"] = "mysql"
    connector: str = Field(default="pymysql", description="数据库连接器")
    pool_size: int = Field(default=10, description="数据库连接池大小", ge=1, le=100)
    max_overflow: int = Field(
        default=20, description="数据库连接池最大超载数量", ge=1, le=100
    )
    pool_timeout: int = Field(
        default=30, description="数据库连接池超时时间", ge=1, le=100
    )
    pool_recycle: int = Field(
        default=3600, description="数据库连接池回收时间", ge=1, le=3600
    )
    pool_pre_ping: bool = Field(default=True, description="数据库连接池预ping")
class DatabaseSettings(BaseSettings):
    database_secret_info: DatabaseSecretInfo = Field(default=DatabaseSecretInfo(),description="数据库密钥信息")
    database_config: DatabaseConfig = Field(default=DatabaseConfig(),description="数据库配置")