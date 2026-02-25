from pydantic_settings import SettingsConfigDict
from .base import TomlBaseSettings
from pydantic import Field, field_validator
from pathlib import Path
class CompressSettings(TomlBaseSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",
        pyproject_toml_table_header=("compress_settings",),
        extra="ignore",
    )
    is_random_salt: bool = Field(default=True, description="是否使用随机盐值")
    compress_password:str = Field(default="H_x123456789", description="压缩密码")
    compress_level: int = Field(default=0, description="压缩级别", ge=0, le=9)
    compress_temp_dir: str = Field(
        default="D:\\backup_compress", description="压缩临时目录"
    )
    compress_salt: dict[int, bytes] = Field(
        default={
            8: b"\xaa%\xec\xec[\x94\xbex",
            12: b"}y\xd5\x19A\xa2\xf6\x1b\xce\x86\x7f\x85",
            16: b"\xd1\x12_\xd7\xd7\n\x92\xfdC\x84\re\xcdxD\x0b",
        },
        description="压缩盐值,长度为8、12、16的bytes",
    )
    compress_chunk_size: int = Field(
        default=200 * 1024 * 1024, description="压缩分块大小,默认200MB"
    )
    exclude_extensions: list[str] = Field(default=[], description="排除的文件扩展名")

    @field_validator("compress_chunk_size", mode="before")
    @classmethod
    def validate_compress_chunk_size(cls, v: int | str) -> int:
        if isinstance(v, str):
            return eval(v, {"__builtins__": None}, {})
        return v
    
    @field_validator("compress_temp_dir")
    @classmethod
    def validate_compress_temp_dir(cls, v: str) -> str:
        temp_path = Path(v)
        temp_path.mkdir(parents=True, exist_ok=True)
        if temp_path.is_file():
            raise FileExistsError(f"压缩临时目录不能是文件: {v}")
        return v