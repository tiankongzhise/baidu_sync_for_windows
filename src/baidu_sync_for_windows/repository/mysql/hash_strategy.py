
from baidu_sync_for_windows.dtos import HashDTO
from baidu_sync_for_windows.models import HashRecord,SourceRecord
from baidu_sync_for_windows.logger import get_logger
from sqlalchemy import text
from .base import RepositoryStrategyInterface


class HashStrategy(
    RepositoryStrategyInterface[
        HashDTO, HashRecord, SourceRecord, SourceRecord
    ]
):
    """HashDTO 的仓储策略，对应 HashRecord / hash_record 表。"""

    def __init__(self) -> None:
        super().__init__(
            HashDTO, HashRecord, SourceRecord, SourceRecord
        )
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})
    def save(self, data: HashDTO) -> HashRecord:
        return self._default_save( data)
    def get_source_record_by_source_id(self, source_id: int) -> SourceRecord | None:
        return self._default_get_source_record_by_source_id( source_id)
    def get_latest_service_record_by_source_id(self, source_id: int) -> SourceRecord | None:
        return self._default_get_latest_service_record_by_source_id( source_id)
    def get_record_by_source_id(self, source_id: int) -> HashRecord | None:
        return self._default_get_record_by_source_id( source_id)
    def is_processed(self, source_id: int) -> bool:
        # 判断source_id的hash_record是否存在，不存在直接返回false
        # 如果存在判断hash_record的更新时间是否为None，如果存在，与source_record的更新时间，如果source_record的更新时间大于hash_record的更新时间，则返回false
        # 如果hash_record的更新时间为None，则比较hash_recor的创建时间与source_recor的更新时间，如果hash_recor的创建时间大于source_recor的更新时间，则返回false
        # 如果source_record的更新时间为None,则比较suore_record的创建时间。
        sql = '''SELECT 
    CASE
        -- 1. hash_record不存在，直接返回false
        WHEN hr.source_id IS NULL THEN FALSE
        -- 2. hash_record更新时间非空的情况
        WHEN hr.updated_at IS NOT NULL THEN
            CASE
                -- source_record更新时间非空，且大于hash_record更新时间 → false
                WHEN sr.updated_at IS NOT NULL AND sr.updated_at > hr.updated_at THEN FALSE
                -- source_record更新时间为空，用创建时间比较，且大于hash_record更新时间 → false
                WHEN sr.updated_at IS NULL AND sr.created_at > hr.updated_at THEN FALSE
                -- 不满足则返回true
                ELSE TRUE
            END
        -- 3. hash_record更新时间为空的情况
        WHEN hr.updated_at IS NULL THEN
            CASE
                -- source_record更新时间非空，且大于hash_record创建时间 → false
                WHEN sr.updated_at IS NOT NULL AND sr.updated_at > hr.created_at THEN FALSE
                -- source_record更新时间为空，用创建时间比较，且大于hash_record创建时间 → false
                WHEN sr.updated_at IS NULL AND sr.created_at > hr.created_at THEN FALSE
                -- 不满足则返回true
                ELSE TRUE
            END
        -- 兜底返回true
        ELSE TRUE
    END AS result
FROM 
    source_record sr
LEFT JOIN 
    hash_record hr ON sr.id = hr.source_id
-- 替换为你要查询的具体source_id
WHERE 
    sr.id = :source_id;'''
        result = self._default_execute_sql(text(sql), source_id=source_id)
        return result.scalar()