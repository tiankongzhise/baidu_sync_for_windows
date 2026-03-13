import threading
from contextlib import contextmanager
from typing import Dict, Optional
from copy import deepcopy
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.repository.mysql import get_repository
from baidu_sync_for_windows.dtos import DiskSpaceCoordinatorDTO
from baidu_sync_for_windows.exception import DiskSpaceCoordinatorServiceException
class DiskSpaceCoordinator:
    """
    支持多类型独立配额的磁盘空间协调器。
    每种资源类型拥有自己的配额，空间不足时申请该类型的线程阻塞。
    """
    def __init__(self, quotas: Dict[str, int]|None=None):
        """
        :param quotas: 字典，键为资源类型，值为该类型的最大可用空间（字节）
        """
        self._lock = threading.RLock()
        self._quotas = deepcopy(quotas) if quotas is not None else deepcopy(get_config().scheduler.quotas)                # 类型 -> 配额
        self._used = {t: 0 for t in self._quotas}        # 类型 -> 已用空间
        # 每种类型拥有独立的条件变量，但共享同一把锁
        self._conds = {t: threading.Condition(self._lock) for t in self._quotas}
        self._repository = get_repository("disk_space_coordinator")
    def _check_type(self, type_: str) -> None:
        """检查资源类型是否存在"""
        if type_ not in self._quotas:
            raise ValueError(f"未知的资源类型: {type_}")

    def acquire(self, type_: str, size: int,source_id: int) -> None:
        """
        申请指定类型的空间，如果不足则阻塞直到有足够空间。
        :param type_: 资源类型
        :param size:  申请大小（字节）
        :param source_id: 源对象ID
        """
        if size <= 0:
            return
        self._check_type(type_)
        with self._conds[type_]:
            while self._used[type_] + size > self._quotas[type_]:
                self._conds[type_].wait()
            self._used[type_] += size
            self._repository.save(DiskSpaceCoordinatorDTO(source_id=source_id, type=type_, disk_space=size, status="acquire"))

    def release(self, type_: str, size: int|None = None,*,source_id: int) -> None:
        """
        释放指定类型的空间，并唤醒所有等待该类型的线程。
        :param type_: 资源类型
        :param size:  释放大小（字节）
        :param source_id: 源对象ID
        """
        if size is None:
            record = self._repository.get_record_by_source_id(source_id,type_)
            if record is None:
                raise DiskSpaceCoordinatorServiceException(f"未找到源对象ID为{source_id}的记录")
            size = record.disk_space
        if size <= 0:
            return
        self._check_type(type_)
        with self._conds[type_]:
            self._used[type_] -= size
            # 防止负值（防御性编程）
            if self._used[type_] < 0:
                self._used[type_] = 0
            self._conds[type_].notify_all()
            self._repository.update(DiskSpaceCoordinatorDTO(source_id=source_id, type=type_, disk_space=size, status="release"))


    @contextmanager
    def reserve(self, type_: str, size: int,source_id: int):
        """
        上下文管理器：自动申请并在退出时释放指定类型的空间。
        适用于临时空间的使用。
        用法：
            with coordinator.reserve('verification', 1024):
                # 执行需要临时空间的操作
        """
        self.acquire(type_, size,source_id)
        try:
            yield
        finally:
            self.release(type_, size,source_id=source_id)


    def get_used(self, type_: Optional[str] = None):
        """
        获取已用空间。若指定类型则返回该类型的值，否则返回所有类型的字典。
        """
        with self._lock:
            if type_ is None:
                return self._used.copy()
            self._check_type(type_)
            return self._used[type_]

    def get_available(self, type_: Optional[str] = None):
        """
        获取剩余空间。若指定类型则返回该类型的值，否则返回所有类型的字典。
        """
        with self._lock:
            if type_ is None:
                return {t: self._quotas[t] - self._used[t] for t in self._quotas}
            self._check_type(type_)
            return self._quotas[type_] - self._used[type_]
    
    def get_unreleased_source_id(self) -> set[int]:
        """
        获取未释放的源对象ID集合。
        """
        with self._lock:
            return set(record.source_id for record in self._repository.get_unreleased_record())