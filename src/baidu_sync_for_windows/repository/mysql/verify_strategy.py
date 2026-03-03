from baidu_sync_for_windows.dtos import VerifyDTO,HashDTO
from baidu_sync_for_windows.models import VerifyRecord,SourceRecord,CompressRecord,HashRecord
from baidu_sync_for_windows.logger import get_logger
from .base import RepositoryStrategyInterface
from sqlalchemy.orm import Session
from typing import Literal

class VerifyStrategy(
    RepositoryStrategyInterface[
        VerifyDTO, VerifyRecord, SourceRecord, CompressRecord
    ]
):
    """VerifyDTO 的仓储策略，对应 VerifyRecord / verify_record 表。"""

    def __init__(self) -> None:
        super().__init__(
            VerifyDTO, VerifyRecord, SourceRecord, CompressRecord
        )
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})
    def save(self, data: VerifyDTO) -> VerifyRecord:
        return self._default_save( data)
    def get_source_record_by_source_id(self, source_id: int) -> SourceRecord | None:
        return self._default_get_source_record_by_source_id( source_id)
    def get_latest_service_record_by_source_id(self, source_id: int) -> CompressRecord | None:
        return self._default_get_latest_service_record_by_source_id( source_id)
    def get_record_by_source_id(self, source_id: int) -> VerifyRecord | None:
        return self._default_get_record_by_source_id( source_id)
    def is_processed(self, source_id: int) -> bool:
        return self._default_is_processed( self.source_record_class, self.record_class, source_id)
    def is_verify_success(self, hash_dto:HashDTO)->Literal['success','failed']:
        with Session(self.engine) as session:
            result = session.query(HashRecord).filter(HashRecord.source_id == hash_dto.source_id,HashRecord.md5 == hash_dto.md5,HashRecord.sha1 == hash_dto.sha1,HashRecord.sha256 == hash_dto.sha256,HashRecord.fast_hash == hash_dto.fast_hash).first()
            if result:
                return 'success'
            else:
                return 'failed'

