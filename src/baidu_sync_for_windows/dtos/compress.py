from pydantic import BaseModel


class CompressDTO(BaseModel):
    source_object_id: int
    compress_object_path: str


class EncryptNameCompressDTO(BaseModel):
    ...