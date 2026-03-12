from redis import Redis
from concurrent.futures import ThreadPoolExecutor,Future
from typing import Any


class RedisCacheService:
    def __init__(self, redis: Redis|None=None, max_workers:int=4,is_set_multi_thread:bool=True,is_get_multi_thread:bool=False):
        self.redis = redis or self._default_redis()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.is_set_multi_thread = is_set_multi_thread
        self.is_get_multi_thread = is_get_multi_thread
    def _default_redis(self) -> Redis:
        return Redis(host='localhost', port=6379, db=0, decode_responses=True)
    @staticmethod
    def _set_worker(r: Redis, key: str, value: Any):
        r.set(key, value)
        return key
    @staticmethod
    def _get_worker(r: Redis, key: str) -> tuple[str, Any]:
        return key,r.get(key)

    def set(self, key: str, value: Any,is_multi_thread:bool|None=None) -> str|Future[str]:
        if is_multi_thread is None:
            is_multi_thread = self.is_set_multi_thread
        if is_multi_thread:
            return self._executor.submit(self._set_worker, self.redis, key, value)
        else:
            return self._set_worker(self.redis, key, value)
    def get(self, key: str,is_multi_thread:bool|None=None) -> Any|Future[tuple[str, Any]]:
        if is_multi_thread is None:
            is_multi_thread = self.is_get_multi_thread
        if is_multi_thread:
            return self._executor.submit(self._get_worker, self.redis, key)
        else:
            key,value = self._get_worker(self.redis, key)
            return value
    
    def flushall(self,*args,**kwargs):
        return self.redis.flushall(*args,**kwargs)
    def flushdb(self,*args,**kwargs):
        return self.redis.flushdb(*args,**kwargs)
