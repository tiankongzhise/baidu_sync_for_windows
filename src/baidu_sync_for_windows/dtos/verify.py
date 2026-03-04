from pydantic import BaseModel,Field,model_validator
from baidu_sync_for_windows.exception import VerifyServiceException
from pathlib import Path
from typing import Literal
class VerifyDTO(BaseModel):
    source_id: int
    verify_compress_file_path: str
    md5: str | None = Field(default=None,description="MD5",min_length=32,max_length=32)
    sha1: str | None = Field(default=None,description="SHA1",min_length=40,max_length=40)
    sha256: str | None = Field(default=None,description="SHA256",min_length=64,max_length=64)
    fast_hash: str | None = Field(default=None,description="Fast Hash")
    verify_result: Literal['success','failed'] = Field(default='failed',description="Verify Result")
    @model_validator(mode='after')
    def validate_verify_fields(self) -> 'VerifyDTO':

        if not Path(self.verify_compress_file_path).exists():
            raise VerifyServiceException(
                f"Verify compress file path {self.verify_compress_file_path} not exists"
            )
        # 收集三大哈希字段的值
        main_hashes = [self.md5, self.sha1, self.sha256]
        # 判断三大哈希字段是否全不为 None
        all_main_hashes_present = all(hash_val is not None for hash_val in main_hashes)
        # 判断三大哈希字段是否全为 None
        all_main_hashes_none = all(hash_val is None for hash_val in main_hashes)
        # 规则1：md5、sha1、sha256 同时存在时，fast_hash 必须为 None
        if all_main_hashes_present:
            if self.fast_hash is not None:
                raise VerifyServiceException(
                    "When md5, sha1, sha256 are all provided, fast_hash must be None"
                )
        # 规则2：md5、sha1、sha256 全为 None 时，fast_hash 不能为 None
        elif all_main_hashes_none:
            if self.fast_hash is None:
                raise VerifyServiceException(
                    "When md5, sha1, sha256 are all None, fast_hash must be provided"
                )
        # 规则3：不允许部分主哈希字段存在的情况
        else:
            raise VerifyServiceException(
                "md5, sha1, sha256 must all be present or all be None"
            )
        return self
class EncryptNameVerifyDTO(BaseModel):
    source_id: int
    encrypt_name_verify_object_path: str
    verify_result: Literal['success','failed'] = Field(default='failed',description="Verify Result")

    @model_validator(mode='after')
    def validate_encrypt_name_verify_fields(self) -> 'EncryptNameVerifyDTO':
        if not Path(self.encrypt_name_verify_object_path).exists():
            raise VerifyServiceException(
                f"Encrypt name verify object path {self.encrypt_name_verify_object_path} not exists"
                )
        return self