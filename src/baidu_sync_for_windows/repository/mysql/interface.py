"""
策略门面：从本模块下加载 *strategy*.py 中的策略类并注册，根据 dto_class 分发到对应策略实例。
"""

from __future__ import annotations

import importlib
from typing import Any, Optional, overload, cast
from pathlib import Path
from baidu_sync_for_windows.exception import RepositoryException
from baidu_sync_for_windows.logger import get_logger
from baidu_sync_for_windows.dtos import (
    ScanDTO,
    CompressDTO,
    VerifyDTO,
    BackupDTO,
    HashDTO,
    EncryptNameCompressDTO,
    EncryptNameVerifyDTO,
    EncryptNameBackupDTO,
)
from baidu_sync_for_windows.models import (
    SourceRecord,
    CompressRecord,
    VerifyRecord,
    BackupRecord,
    HashRecord,
    EncryptNameCompressRecord,
    EncryptNameVerifyRecord,
    EncryptNameBackupRecord,
    ServiceBase,
)
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from .base import RepositoryStrategyInterface, DTOClass, Record, DTO


import inspect
from typing import Dict
logger = get_logger(bind={"module_name": "MysqlRepository"})

# ---------- 策略管理器 ----------
class StrategyManager:
    """
    策略管理器，负责动态加载策略文件并管理策略实例。

    策略文件存放位置：默认位于本模块所在目录下的 'strategies' 子目录，
    如果该目录不存在，则直接使用本模块所在目录。
    文件名必须以 '_strategy.py' 结尾（可通过类属性修改）。
    """

    # 策略文件的后缀，可被子类覆盖
    STRATEGY_FILE_SUFFIX = "_strategy.py"

    def __init__(self, strategy_dir: Optional[str] = None):
        """
        初始化策略管理器。
        :param strategy_dir: 策略文件所在目录。若为 None，则自动定位。
        """
        self.logger = get_logger(bind={"module_name": self.__class__.__name__})
        self._strategies: Dict[
            DTOClass, RepositoryStrategyInterface
        ] = {}  # 入参类型 -> 策略实例
        self._strategy_dir = self._determine_strategy_dir(strategy_dir)
        self.load_strategies()

    def _determine_strategy_dir(self, custom_dir: Optional[str]) -> Path:
        """确定策略文件所在的目录"""
        if custom_dir:
            self.logger.info(f"确定策略文件所在的目录: {custom_dir}")
            return Path(custom_dir)
        self.logger.info(f"确定策略文件所在的目录: {Path(__file__).parent}")
        return Path(__file__).parent

    def _is_strategy_class(self, obj: Any) -> bool:
        """判断一个对象是否为合法的策略类（继承自 Strategy 且非抽象）"""

        result = (
            inspect.isclass(obj)
            and issubclass(obj, RepositoryStrategyInterface)
            and obj is not RepositoryStrategyInterface
            and not inspect.isabstract(obj)
        )
        self.logger.debug(f"判断一个对象是否为合法的策略类: {obj}: {result}")
        return result

    def _load_strategy_module(self, module_name: str):
        """
        以当前包子模块方式加载策略模块，使模块内相对引用（如 from .base import ...）生效。
        返回加载的模块，失败返回 None。
        """
        # 使用包内子模块名加载，保证相对导入有父包
        full_module_name = f"{__package__}.{module_name}"
        try:
            self.logger.info(f"加载模块: {full_module_name}")
            return importlib.import_module(full_module_name)
        except Exception as e:
            self.logger.error(f"加载模块 {full_module_name} 时出错：{e}")
            return None

    def load_strategies(self, force_reload: bool = False) -> None:
        """
        加载所有策略文件中的策略类并注册为实例。
        :param force_reload: 是否强制重新加载（清空现有策略）
        """
        if force_reload:
            self._strategies.clear()

        # 遍历指定目录下所有匹配后缀的文件，按包内子模块加载以支持相对引用
        for file_path in self._strategy_dir.glob("*.py"):
            if self.STRATEGY_FILE_SUFFIX not in file_path.name:
                self.logger.debug(f"跳过文件: {file_path.name}，不是策略文件")
                continue
            module_name = file_path.stem
            module = self._load_strategy_module(module_name)
            if module is None:
                self.logger.error(f"加载模块 {module_name} 时出错：{module}")
                continue

            # 遍历模块中的属性，找出所有策略类
            for name, obj in inspect.getmembers(module,predicate=inspect.isclass):
                # 跳过不是模块内的类
                if obj.__module__ != module.__name__:
                    self.logger.debug(f"跳过对象: {name}，不是模块内的类")
                    continue

                if not self._is_strategy_class(obj):
                    self.logger.debug(f"跳过对象: {name}，不是策略类")
                    continue

                # 实例化策略（假定无参构造）
                try:
                    strategy_instance = obj()
                    self.logger.info(f"实例化策略类: {obj.__name__}")
                except Exception as e:
                    self.logger.error(f"实例化策略类 {obj.__name__} 时出错：{e}")
                    continue

                # 注册：使用策略对象的 dto_class 属性作为键
                key = strategy_instance.dto_class
                if key in self._strategies:
                    self.logger.warning(
                        f"警告：策略 dto_class '{key}' 重复，后面的将覆盖前面的"
                    )
                self._strategies[key] = strategy_instance

        self.logger.info(
            f"策略加载完成，共 {len(self._strategies)} 个策略：{list(self._strategies.keys())}"
        )

    def get_strategy(
        self, dto_class: DTOClass|None=None
    ) -> RepositoryStrategyInterface:
        """根据dto_class获取策略实例,如果dto_class为None,则返回第一个策略实例"""
        self.logger.debug(f"根据dto_class获取策略实例: {dto_class}")
        if dto_class is None:
            defualt_dto_class = self.list_strategies()[0]
            if not defualt_dto_class:
                raise RepositoryException("No strategies registered")
            strategy = self._strategies.get(defualt_dto_class)
            self.logger.debug(f"get strategy: {strategy}")
            if strategy is None:
                raise RepositoryException(f"No strategy registered for DTO type: {defualt_dto_class.__name__}")
            return cast(RepositoryStrategyInterface, strategy)
        else:
            strategy = self._strategies.get(dto_class)
            self.logger.debug(f"get strategy: {strategy}")
            if strategy is None:
                raise RepositoryException(f"No strategy registered for DTO type: {dto_class.__name__}")
        return strategy
    def list_strategies(self) -> list:
        """返回所有已注册的策略名称列表"""
        self.logger.debug(
            f"返回所有已注册的策略名称列表: {list(self._strategies.keys())}"
        )
        return list(self._strategies.keys())

strategy_manager = None

def get_strategy_manager() -> StrategyManager:
    global strategy_manager
    if strategy_manager is None:
        strategy_manager = StrategyManager()
    return strategy_manager


class MysqlRepository(object):
    engine: Engine
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.logger = logger
        self._strategy_manager = get_strategy_manager()
        self._test_connection()
    # 私有方法

    def _test_connection(self) -> None:
        try:
            with Session(self.engine) as session:
                session.execute(text("SELECT 1"))
                session.commit()
                self.logger.info("Connection test successful")
        except Exception as e:
            self.logger.error(f"Failed to test connection: {e}")
            raise RepositoryException(f"Failed to test connection: {e}") from e

    def create_tables(self) -> None:
        self.logger.info("创建表")
        ServiceBase.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        self.logger.info("删除表")
        ServiceBase.metadata.drop_all(self.engine)

    def reset_tables(self) -> None:
        self.logger.info("重置表")
        self.drop_tables()
        self.create_tables()

    def _get_strategy(self, dto_class: DTOClass) -> RepositoryStrategyInterface:
        strategy = self._strategy_manager.get_strategy(dto_class)
        if strategy is None:
            self.logger.error(
                f"No strategy registered for DTO type: {dto_class.__name__}. Available strategies: {self._strategy_manager.list_strategies()}"
            )
            raise RepositoryException(
                f"No strategy registered for DTO type: {dto_class.__name__}. "
                f"Available strategies: {self._strategy_manager.list_strategies()}"
            )
        return strategy
    # 重载定义区域
    @overload
    def save(self, data: ScanDTO) -> SourceRecord: ...
    @overload
    def save(self, data: CompressDTO) -> CompressRecord: ...
    @overload
    def save(self, data: VerifyDTO) -> VerifyRecord: ...
    @overload
    def save(self, data: BackupDTO) -> BackupRecord: ...
    @overload
    def save(self, data: HashDTO) -> HashRecord: ...
    @overload
    def save(self, data: EncryptNameCompressDTO) -> EncryptNameCompressRecord: ...
    @overload
    def save(self, data: EncryptNameVerifyDTO) -> EncryptNameVerifyRecord: ...
    @overload
    def save(self, data: EncryptNameBackupDTO) -> EncryptNameBackupRecord: ...


    @overload
    def get_source_record_by_source_id(self, dto_class: type[ScanDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_source_record_by_source_id(self, dto_class: type[CompressDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_source_record_by_source_id(self, dto_class: type[VerifyDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_source_record_by_source_id(self, dto_class: type[BackupDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_source_record_by_source_id(self, dto_class: type[HashDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_source_record_by_source_id(self, dto_class: type[EncryptNameCompressDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_source_record_by_source_id(self, dto_class: type[EncryptNameVerifyDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_source_record_by_source_id(self, dto_class: type[EncryptNameBackupDTO],id: int) -> Optional[SourceRecord]: ...

    @overload
    def get_latest_service_record_by_source_id(self, dto_class: type[ScanDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_latest_service_record_by_source_id(self, dto_class: type[HashDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_latest_service_record_by_source_id(self, dto_class: type[CompressDTO],id: int) -> Optional[HashRecord]: ...
    @overload
    def get_latest_service_record_by_source_id(self, dto_class: type[VerifyDTO],id: int) -> Optional[CompressRecord]: ...
    @overload
    def get_latest_service_record_by_source_id(self, dto_class: type[BackupDTO],id: int) -> Optional[VerifyRecord]: ...
    @overload
    def get_latest_service_record_by_source_id(self, dto_class: type[EncryptNameCompressDTO],id: int) -> Optional[HashRecord]: ...
    @overload
    def get_latest_service_record_by_source_id(self, dto_class: type[EncryptNameVerifyDTO],id: int) -> Optional[EncryptNameCompressRecord]: ...
    @overload
    def get_latest_service_record_by_source_id(self, dto_class: type[EncryptNameBackupDTO],id: int) -> Optional[EncryptNameVerifyRecord]: ...

    @overload
    def get_record_by_source_id(self, dto_class: type[ScanDTO],id: int) -> Optional[SourceRecord]: ...
    @overload
    def get_record_by_source_id(self, dto_class: type[HashDTO],id: int) -> Optional[HashRecord]: ...
    @overload
    def get_record_by_source_id(self, dto_class: type[CompressDTO],id: int) -> Optional[CompressRecord]: ...
    @overload
    def get_record_by_source_id(self, dto_class: type[VerifyDTO],id: int) -> Optional[VerifyRecord]: ...
    @overload
    def get_record_by_source_id(self, dto_class: type[BackupDTO],id: int) -> Optional[BackupRecord]: ...
    @overload
    def get_record_by_source_id(self, dto_class: type[EncryptNameCompressDTO],id: int) -> Optional[EncryptNameCompressRecord]: ...
    @overload
    def get_record_by_source_id(self, dto_class: type[EncryptNameVerifyDTO],id: int) -> Optional[EncryptNameVerifyRecord]: ...
    @overload
    def get_record_by_source_id(self, dto_class: type[EncryptNameBackupDTO],id: int) -> Optional[EncryptNameBackupRecord]: ...
    # 重载实现区域

    def save(self, data: DTO) -> Record:
        strategy = self._get_strategy(type(data))
        result = strategy.save(self, data)
        self.logger.log("MODULE_INFO",f"save data: {data.model_dump()} result: {result}")
        return result

    def get_source_record_by_source_id(self, dto_class: DTOClass,id: int) -> Optional[Record]:
        strategy = self._get_strategy(dto_class)
        result = strategy.get_source_record_by_source_id(self, id)
        self.logger.log("MODULE_INFO",f"get source record by source id: {id} result: {result}")
        return result
    def get_latest_service_record_by_source_id(self, dto_class: DTOClass,id: int) -> Optional[Record]:
        strategy = self._get_strategy(dto_class)
        result = strategy.get_latest_service_record_by_source_id(self, id)
        self.logger.log("MODULE_INFO",f"get latest service record by source id: {id} result: {result}")
        return result
    def get_record_by_source_id(self, dto_class: DTOClass,id: int) -> Optional[Record]:
        strategy = self._get_strategy(dto_class)
        result = strategy.get_record_by_source_id(self, id)
        self.logger.log("MODULE_INFO",f"get record by source id: {id} result: {result}")
        return result
    

