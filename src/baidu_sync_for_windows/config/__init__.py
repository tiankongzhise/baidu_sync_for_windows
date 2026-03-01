from .database import DatabaseSettings
from .scan import ScanSettings
from .hash import HashSettings
from .compress import CompressSettings
from .verify import VerifierSettings
from .logger import LoggingSettings
from .oauth import BaiduPanOAuthSettings
from .upload import BaiduPanUploadSettings
from .base import drive_letter
from pydantic_settings import BaseSettings
from pydantic import Field
from .source import SourcePathSettings



class ConfigSettings(BaseSettings):
    drive_letter: str = Field(default=drive_letter(), description="驱动器字母")
    source_path: SourcePathSettings = Field(default=SourcePathSettings(), description="源路径设置")
    database: DatabaseSettings = Field(default=DatabaseSettings(), description="数据库设置")
    scan: ScanSettings = Field(default=ScanSettings(), description="扫描设置")
    hash: HashSettings = Field(default=HashSettings(), description="哈希设置")
    compress: CompressSettings = Field(default=CompressSettings(), description="压缩设置")
    verify: VerifierSettings = Field(default=VerifierSettings(), description="验证设置")
    logger: LoggingSettings = Field(default=LoggingSettings(), description="日志设置")
    oauth: BaiduPanOAuthSettings = Field(default=BaiduPanOAuthSettings(), description="OAuth设置")
    upload: BaiduPanUploadSettings = Field(default=BaiduPanUploadSettings(), description="上传设置")

config = None
def get_config() -> ConfigSettings:
    global config
    if config is None:
        config = ConfigSettings()
    return config
