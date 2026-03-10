from baidu_sync_for_windows.dtos import EncryptNameCompressDTO
from baidu_sync_for_windows.models import (
    EncryptNameCompressRecord,
    SourceRecord,
    HashRecord,
)
from baidu_sync_for_windows.logger import get_logger
from sqlalchemy.orm import Session
from .base import RepositoryStrategyInterface


class EncryptNameCompressStrategy(
    RepositoryStrategyInterface[
        EncryptNameCompressDTO,
        EncryptNameCompressRecord,
        SourceRecord,
        HashRecord,
    ]
):
    """EncryptNameCompressDTO 的仓储策略，对应 EncryptNameCompressRecord / encrypt_name_compress_record 表。"""

    def __init__(self) -> None:
        super().__init__(
            EncryptNameCompressDTO,
            EncryptNameCompressRecord,
            SourceRecord,
            HashRecord,
        )
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})

    def save(self, data: EncryptNameCompressDTO) -> EncryptNameCompressRecord:
        return self._default_save(data)

    def get_source_record_by_source_id(self, source_id: int) -> SourceRecord | None:
        return self._default_get_source_record_by_source_id(source_id)

    def get_latest_service_record_by_source_id(
        self, source_id: int
    ) -> HashRecord | None:
        return self._default_get_latest_service_record_by_source_id(source_id)

    def get_record_by_source_id(
        self, source_id: int
    ) -> EncryptNameCompressRecord | None:
        return self._default_get_record_by_source_id(source_id)

    def is_processed(self, source_id: int) -> bool:
        return self._default_is_processed(
            self.source_record_class, self.record_class, source_id
        )

    def is_encrypt_name_used(self, encrypt_name: str) -> bool:
        with Session(self.engine) as session:
            record = (
                session.query(self.record_class)
                .filter(self.record_class.encrypt_file_name == encrypt_name)
                .first()
            )
            return record is not None