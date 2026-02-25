from pydantic_settings import SettingsConfigDict
from .base import TomlBaseSettings
from pydantic import Field
class BaiduPanUploadSettings(TomlBaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        pyproject_toml_table_header=("baidu_pan_upload_settings",),
        extra="ignore",
    )
    block_size: int = Field(default=30 * 1024 * 1024, description="分片大小,默认30MB")
    algorithm: str = Field(default="md5", description="哈希算法")
    remote_path: str = Field(default="/(1test)", description="远程路径")
    upload_concurrency: int = Field(default=5, description="上传并发数", ge=1)
    max_block_retries: int = Field(default=3, description="单个分片最大重试次数", ge=1)
    upload_timeout: int = Field(default=3000, description="上传超时时间", ge=1)
    existing_file_policy: int = Field(default=1, description="云端文件存在策略", ge=0, le=3)
    is_crash_on_upload_failed: bool = Field(default=True, description="上传失败时是否立刻崩溃,默认True")
    is_crash_on_create_remote_file: bool = Field(default=True, description="创建远程文件失败时是否立刻崩溃,默认True")

