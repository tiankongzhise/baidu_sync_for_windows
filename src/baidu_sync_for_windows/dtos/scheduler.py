from pydantic import BaseModel,Field
from typing import Literal
class DiskSpaceCoordinatorDTO(BaseModel):
    source_id: int = Field(..., description="源对象ID")
    type: str = Field(..., description="类型")
    disk_space: int = Field(..., description="磁盘空间", ge=0)
    status: Literal["acquire", "release"] = Field(..., description="状态")
