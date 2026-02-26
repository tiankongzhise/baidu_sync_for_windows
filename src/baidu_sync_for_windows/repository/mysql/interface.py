"""
策略门面：从本模块下加载 *strategy*.py 中的策略类并注册，根据 dto_class 分发到对应策略实例。
"""
from __future__ import annotations

import importlib
from typing import Any, Type, Optional, overload
from pathlib import Path
from baidu_sync_for_windows.exception import RepositoryException
from baidu_sync_for_windows.logger import get_logger
from baidu_sync_for_windows.dtos import ScanDTO, CompressDTO, VerifyDTO, BackupDTO, HashDTO, EncryptNameCompressDTO, EncryptNameVerifyDTO, EncryptNameBackupDTO
from baidu_sync_for_windows.models import SourceObjectRecord, ObjectCompressRecord, ObjectVerifyRecord, ObjectBackupRecord, ObjectHashRecord, ObjectEncryptNameCompressRecord, ObjectEncryptNameVerifyRecord, ObjectEncryptNameBackupRecord,ServiceBase
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session


from .base import RepositoryStrategyInterface, DTO, Record




import inspect
from abc import ABC, abstractmethod
from typing import Dict, Type, Any, Optional



# ---------- 策略管理器 ----------
class StrategyManager:
    """
    策略管理器，负责动态加载策略文件并管理策略实例。
    
    策略文件存放位置：默认位于本模块所在目录下的 'strategies' 子目录，
    如果该目录不存在，则直接使用本模块所在目录。
    文件名必须以 '_strategy.py' 结尾（可通过类属性修改）。
    """
    
    # 策略文件的后缀，可被子类覆盖
    STRATEGY_FILE_SUFFIX = '_strategy.py'
    
    def __init__(self, strategy_dir: Optional[str] = None):
        """
        初始化策略管理器。
        :param strategy_dir: 策略文件所在目录。若为 None，则自动定位。
        """
        self._strategies: Dict[DTO, RepositoryStrategyInterface] = {}  # 入参类型 -> 策略实例
        self._strategy_dir = self._determine_strategy_dir(strategy_dir)
        self.load_strategies()
    
    def _determine_strategy_dir(self, custom_dir: Optional[str]) -> Path:
        """确定策略文件所在的目录"""
        if custom_dir:
            return Path(custom_dir)
        return Path(__file__).parent
    
    def _is_strategy_class(self, obj: Any) -> bool:
        """判断一个对象是否为合法的策略类（继承自 Strategy 且非抽象）"""
        return (inspect.isclass(obj) 
                and issubclass(obj, RepositoryStrategyInterface) 
                and obj is not RepositoryStrategyInterface
                and not inspect.isabstract(obj))
    
    def _load_strategy_module(self, module_name: str):
        """
        以当前包子模块方式加载策略模块，使模块内相对引用（如 from .base import ...）生效。
        返回加载的模块，失败返回 None。
        """
        # 使用包内子模块名加载，保证相对导入有父包
        full_module_name = f"{__package__}.{module_name}"
        try:
            return importlib.import_module(full_module_name)
        except Exception as e:
            print(f"加载模块 {full_module_name} 时出错：{e}")
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
                continue
            module_name = file_path.stem
            module = self._load_strategy_module(module_name)
            if module is None:
                continue
            
            # 遍历模块中的属性，找出所有策略类
            for name, obj in inspect.getmembers(module):
                if not self._is_strategy_class(obj):
                    continue
                
                # 实例化策略（假定无参构造）
                try:
                    strategy_instance = obj()
                except Exception as e:
                    print(f"实例化策略类 {obj.__name__} 时出错：{e}")
                    continue
                
                # 注册：使用策略对象的 dto_class 属性作为键
                key = strategy_instance.dto_class
                if key in self._strategies:
                    print(f"警告：策略 dto_class '{key}' 重复，后面的将覆盖前面的")
                self._strategies[key] = strategy_instance
        
        print(f"策略加载完成，共 {len(self._strategies)} 个策略：{list(self._strategies.keys())}")
    
    
    def get_strategy(self, dto_class: Type[DTO]) -> Optional[RepositoryStrategyInterface]:
        """根据名称获取策略实例"""
        return self._strategies.get(dto_class)
    
    def list_strategies(self) -> list:
        """返回所有已注册的策略名称列表"""
        return list(self._strategies.keys())
    








class MysqlRepository(object):

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.logger = get_logger(bind={"repository_name": "mysql"})
        self._strategy_manager = StrategyManager()
        self._test_connection()

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
        ServiceBase.metadata.create_all(self.engine)
    def drop_tables(self) -> None:
        ServiceBase.metadata.drop_all(self.engine)
    def reset_tables(self) -> None:
        self.drop_tables()
        self.create_tables()
    @overload
    def save(self, data: ScanDTO) -> SourceObjectRecord:...
    @overload
    def save(self, data: CompressDTO) -> ObjectCompressRecord:...
    @overload
    def save(self, data: VerifyDTO) -> ObjectVerifyRecord:...
    @overload
    def save(self, data: BackupDTO) -> ObjectBackupRecord:...
    @overload
    def save(self, data: HashDTO) -> ObjectHashRecord:...
    @overload
    def save(self, data: EncryptNameCompressDTO) -> ObjectEncryptNameCompressRecord:...
    @overload
    def save(self, data: EncryptNameVerifyDTO) -> ObjectEncryptNameVerifyRecord:...
    @overload
    def save(self, data: EncryptNameBackupDTO) -> ObjectEncryptNameBackupRecord:...


















































    def save(self, data: DTO) -> Optional[Record]:
        strategy = self._strategy_manager.get_strategy(type(data))
        if strategy is None:
            raise RepositoryException(
                f"No strategy registered for DTO type: {type(data).__name__}. "
                f"Available strategies: {self._strategy_manager.list_strategies()}"
            )
        return strategy.save(self, data)
    def get_by_id(self, id: int, dto_class: Type[DTO]) -> Optional[Record]:
        strategy = self._strategy_manager.get_strategy(dto_class)
        if strategy is None:
            raise RepositoryException(
                f"No strategy registered for DTO type: {dto_class.__name__}. "
                f"Available strategies: {self._strategy_manager.list_strategies()}"
            )
        return strategy.get_by_source_object_id(self, id)