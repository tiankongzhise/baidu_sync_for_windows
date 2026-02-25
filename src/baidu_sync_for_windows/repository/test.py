from __future__ import annotations

from typing import (
    Any,
    Dict,
    Optional,
    Type,
    TypeVar,
    Union,
    Generic,
    Protocol,
    runtime_checkable,
)
from dataclasses import dataclass

# 前置导入（保持原有）
from baidu_sync_for_windows.dtos import (
    ScanDTO, CompressDTO, VerifyDTO, BackupDTO, HashDTO,
    EncryptNameCompressDTO, EncryptNameVerifyDTO, EncryptNameBackupDTO
)
from baidu_sync_for_windows.models import (
    OauthRecord, SourceObjectRecord, ObjectHashRecord, ObjectCompressRecord,
    ObjectVerifyRecord, ObjectBackupRecord, ObjectEncryptNameCompressRecord,
    ObjectEncryptNameVerifyRecord, ObjectEncryptNameBackupRecord
)
from baidu_sync_for_windows.exception import RepositoryException
from baidu_sync_for_windows.logger import get_logger
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

# ====================== 1. 泛型类型与抽象策略接口 ======================
DTO = TypeVar("DTO", contravariant=True)  # 逆变：用于入参
Record = TypeVar("Record", covariant=True)  # 协变：用于返回值

@runtime_checkable
class RepositoryStrategy(Protocol[DTO, Record]):
    """
    抽象策略接口：定义所有策略必须实现的方法
    基于Protocol的接口隔离，无需继承，只需实现对应方法
    """
    @property
    def dto_cls(self) -> Type[DTO]:
        """返回对应的DTO类"""
        ...
    
    @property
    def record_cls(self) -> Type[Record]:
        """返回对应的Record类"""
        ...
    
    def save(self, repo: MysqlRepository, dto: DTO) -> None:
        """保存DTO的业务逻辑（可选实现）"""
        ...
    
    def get_by_id(self, repo: MysqlRepository, id: int) -> Optional[Record]:
        """按ID查询Record的业务逻辑（可选实现）"""
        ...

# ====================== 2. 策略注册表（自动注册+全局调度） ======================
class StrategyRegistry:
    """策略注册表：单例+自动注册，完全解耦策略与Repository"""
    _instance: Optional[StrategyRegistry] = None
    _dto_strategies: Dict[Type[Any], RepositoryStrategy[Any, Any]] = {}
    _record_strategies: Dict[Type[Any], RepositoryStrategy[Any, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_strategy(cls, strategy: RepositoryStrategy[Any, Any]):
        """注册策略（通过装饰器调用）"""
        cls._dto_strategies[strategy.dto_cls] = strategy
        cls._record_strategies[strategy.record_cls] = strategy
    
    def get_strategy_by_dto(self, dto_cls: Type[DTO]) -> RepositoryStrategy[DTO, Record]:
        """根据DTO类获取策略"""
        strategy = self._dto_strategies.get(dto_cls)
        if not strategy:
            raise RepositoryException(f"No strategy found for DTO: {dto_cls.__name__}")
        return strategy

# 策略注册装饰器（核心：新增策略只需加装饰器）
def register_repository_strategy(strategy_cls: Type[RepositoryStrategy[Any, Any]]):
    """装饰器：自动注册策略类实例"""
    strategy_instance = strategy_cls()
    StrategyRegistry.register_strategy(strategy_instance)
    return strategy_cls

# ====================== 3. 具体策略类（每个DTO/Record独立维护） ======================
# 3.1 ScanDTO 策略（独立文件/模块中维护）
@register_repository_strategy
class ScanDTOStrategy(RepositoryStrategy[ScanDTO, SourceObjectRecord]):
    """ScanDTO专属策略：所有业务逻辑在此维护"""
    @property
    def dto_cls(self) -> Type[ScanDTO]:
        return ScanDTO
    
    @property
    def record_cls(self) -> Type[SourceObjectRecord]:
        return SourceObjectRecord
    
    def save(self, repo: MysqlRepository, dto: ScanDTO) -> None:
        """ScanDTO的保存逻辑"""
        with Session(repo.engine) as session:
            # 此处写ScanDTO -> SourceObjectRecord的具体保存逻辑
            record = SourceObjectRecord(
                drive_letter=dto.drive_letter,
                target_object_path=dto.target_object_path,
                scan_time=dto.scan_time
                # 其他字段映射...
            )
            session.add(record)
            session.commit()
            repo.logger.info(f"ScanDTO saved: {dto.target_object_path}")
    
    def get_by_id(self, repo: MysqlRepository, id: int) -> Optional[SourceObjectRecord]:
        """按ID查询SourceObjectRecord的逻辑"""
        with Session(repo.engine) as session:
            return session.query(SourceObjectRecord).filter_by(id=id).first()

# 3.2 CompressDTO 策略（独立维护）
@register_repository_strategy
class CompressDTOStrategy(RepositoryStrategy[CompressDTO, ObjectCompressRecord]):
    """CompressDTO专属策略"""
    @property
    def dto_cls(self) -> Type[CompressDTO]:
        return CompressDTO
    
    @property
    def record_cls(self) -> Type[ObjectCompressRecord]:
        return ObjectCompressRecord
    
    def save(self, repo: MysqlRepository, dto: CompressDTO) -> None:
        """CompressDTO的保存逻辑"""
        with Session(repo.engine) as session:
            record = ObjectCompressRecord(
                source_object_id=dto.source_object_id,
                compress_path=dto.compress_path,
                compress_size=dto.compress_size
                # 其他字段映射...
            )
            session.add(record)
            session.commit()
            repo.logger.info(f"CompressDTO saved: {dto.compress_path}")
    
    def get_by_id(self, repo: MysqlRepository, id: int) -> Optional[ObjectCompressRecord]:
        """按ID查询ObjectCompressRecord的逻辑"""
        with Session(repo.engine) as session:
            return session.query(ObjectCompressRecord).filter_by(id=id).first()

# 3.3 其他策略类（示例：EncryptNameCompressDTO）
@register_repository_strategy
class EncryptNameCompressDTOStrategy(RepositoryStrategy[EncryptNameCompressDTO, ObjectEncryptNameCompressRecord]):
    """EncryptNameCompressDTO专属策略（仅查询）"""
    @property
    def dto_cls(self) -> Type[EncryptNameCompressDTO]:
        return EncryptNameCompressDTO
    
    @property
    def record_cls(self) -> Type[ObjectEncryptNameCompressRecord]:
        return ObjectEncryptNameCompressRecord
    
    def get_by_id(self, repo: MysqlRepository, id: int) -> Optional[ObjectEncryptNameCompressRecord]:
        """按ID查询加密压缩记录"""
        with Session(repo.engine) as session:
            return session.query(ObjectEncryptNameCompressRecord).filter_by(id=id).first()

# 更多策略类（VerifyDTO/BackupDTO/HashDTO等）按相同模式编写...

# ====================== 4. 极简的MysqlRepository（仅调度，无业务逻辑） ======================
class MysqlRepository:
    """
    核心Repository：仅做策略调度，无任何具体业务逻辑
    新增DTO/Record时，无需修改此类
    """
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.logger = get_logger(bind={"repository_name": "mysql"})
        self._strategy_registry = StrategyRegistry()
        self._test_connection()

    # ---------- 对外统一接口（泛型+重载，IDE提示完美） ----------
    def save(self, dto: DTO) -> None:
        """
        统一保存接口：
        - 自动匹配策略
        - 调用策略的save方法
        - 完全无需修改此方法即可支持新DTO
        """
        try:
            strategy = self._strategy_registry.get_strategy_by_dto(type(dto))
            strategy.save(self, dto)
        except Exception as e:
            self.logger.error(f"Failed to save {type(dto).__name__}: {str(e)}")
            raise RepositoryException(f"Save failed: {str(e)}") from e

    def get_by_id(self, id: int, dto_type: Type[DTO]) -> Optional[Record]:
        """统一按ID查询接口"""
        try:
            strategy = self._strategy_registry.get_strategy_by_dto(dto_type)
            return strategy.get_by_id(self, id)
        except Exception as e:
            self.logger.error(f"Failed to get {dto_type.__name__} by id {id}: {str(e)}")
            raise RepositoryException(f"Get failed: {str(e)}") from e

    # ---------- 专用接口（非DTO/Record映射的独立逻辑） ----------
    def get_oauth(self, platform: str) -> Optional[OauthRecord]:
        """Oauth查询（独立逻辑，可封装为单独策略）"""
        with Session(self.engine) as session:
            return session.query(OauthRecord).filter_by(platform=platform).first()

    def get_source_object(self, drive_letter: str, path: str) -> Optional[SourceObjectRecord]:
        """按路径查询SourceObject（独立逻辑）"""
        with Session(self.engine) as session:
            return session.query(SourceObjectRecord).filter_by(
                drive_letter=drive_letter,
                target_object_path=path
            ).first()

    # ---------- 内部辅助方法（无业务逻辑） ----------
    def _test_connection(self) -> None:
        """测试数据库连接"""
        try:
            with Session(self.engine) as session:
                session.execute(text("SELECT 1"))
                session.commit()
                self.logger.info("Database connection test successful")
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            raise RepositoryException(f"DB connection failed: {str(e)}") from e

    # ---------- 通用数据库操作（供策略类调用） ----------
    def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """通用SQL执行方法"""
        with Session(self.engine) as session:
            result = session.execute(text(query), params or {})
            session.commit()
            return result

    def insert(self, record: Any) -> None:
        """通用插入方法（策略类可复用）"""
        with Session(self.engine) as session:
            session.add(record)
            session.commit()

    def update(self, record: Any) -> None:
        """通用更新方法（策略类可复用）"""
        with Session(self.engine) as session:
            session.merge(record)
            session.commit()