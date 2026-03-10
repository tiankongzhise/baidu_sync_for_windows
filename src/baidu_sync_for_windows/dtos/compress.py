from pydantic import BaseModel,Field,field_validator
from baidu_sync_for_windows.exception import CompressServiceException
from pathlib import Path
class CompressDTO(BaseModel):
    source_id: int
    compress_file_path: str
    
    @field_validator("compress_file_path")
    @classmethod
    def validate_compress_file_path(cls, v: str) -> str:
        compress_file_path = Path(v)
        if not compress_file_path.exists():
            raise CompressServiceException(f"Compress file path {v} does not exist")
        return v


class EncryptNameCompressDTO(BaseModel):
    source_id: int
    origin_file_name: str
    encrypt_file_name: str
    compress_file_path: str

    @field_validator("compress_file_path")
    @classmethod
    def validate_compress_file_path(cls, v: str) -> str:
        compress_file_path = Path(v)
        if not compress_file_path.exists():
            raise CompressServiceException(f"Compress file path {v} does not exist")
        return v
