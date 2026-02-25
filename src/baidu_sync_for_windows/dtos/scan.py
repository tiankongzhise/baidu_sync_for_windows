from pydantic import BaseModel
from pydantic import Field, field_validator
from pathlib import Path
from typing import Literal
from baidu_sync_for_windows.exception import ScanServiceException
from datetime import datetime
class ScanDTO(BaseModel):
    drive_letter: str = Field(..., description="驱动器字母")
    target_object_path: str = Field(..., description="目标对象路径")
    target_object_name: str = Field(..., description="目标对象名称")
    target_object_type: str = Field(..., description="目标对象类型")
    target_object_size: int = Field(..., description="目标对象大小")
    target_object_items_count: int = Field(..., description="目标对象项数")
    target_object_items: dict[str,int] = Field(..., description="目标对象项")
    process_type: Literal['auto','manual'] = Field(..., description="处理类型")

    @field_validator("target_object_path")
    @classmethod
    def validate_target_object_path(cls, v: str) -> str:
        temp_path = Path(v)
        if not temp_path.exists():
            raise ScanServiceException(f"目标对象{v}路径不存在")
        return v

    @field_validator("target_object_items")
    @classmethod
    def validate_target_object_items(cls, v: dict[str,int]) -> dict[str,int]:
        for key,value in v.items():
            if not Path(key).exists():
                raise ScanServiceException(f"目标对象项{key}路径不存在")
            try:
                datetime.fromtimestamp(value / 1_000_000_000)
            except Exception as e:
                raise ScanServiceException(f"目标对象项{key}时间戳格式错误: {e}")
        return v