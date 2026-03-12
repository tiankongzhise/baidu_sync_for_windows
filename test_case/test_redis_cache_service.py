from baidu_sync_for_windows.cache.redis_cache import RedisCacheService
import random
import pathlib
import json
from concurrent.futures import as_completed
from baidu_sync_for_windows.utils import benchmark_time
def create_random_data():
    redis_test_data = pathlib.Path('redis_test_data.json')
    if redis_test_data.exists():
        return 
    data = {}
    for _ in range(10000):
        data[f'test_{random.randint(1, 1000000)}'] = f'value_{random.randint(1, 1000000)}'
    with open(redis_test_data, 'w') as f:
        json.dump(data, f)
    print(f'create {len(data.keys())} data success')
    return redis_test_data
def get_random_data()->dict[str, str]|None:
    redis_test_data = pathlib.Path('redis_test_data.json')
    if not redis_test_data.exists():
        return None
    with open(redis_test_data, 'r') as f:
        data = json.load(f)
    print(f'get {len(data.keys())} data success')
    return data


def test_get_after_redis_restart():
    r = RedisCacheService()
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    for key, value in data.items():
        result = r.get(key)
        if result != value:
            raise Exception(f"get {key} {result} ,expected {value} failed")
        print(f"get {key} {result} ,expected {value} success", end="\r")
    print('\n')
    print(f"get {len(data.keys())} data success")

def test_set_and_get_multi_thread():
    r = RedisCacheService()
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    results = []
    for key, _ in data.items():
        results.append(r.get(key,is_multi_thread=True))
    for result in as_completed(results):
        key,result = result.result()
        if result != data[key]:
            raise Exception(f"get {key} {result} ,expected {data[key]} failed")
        print(f"get {key} {result} ,expected {data[key]} success", end="\r")
    print('\n')
    print(f"set {len(data.keys())} data success")

def test_flushall(*args,**kwargs):
    r = RedisCacheService()
    result = r.flushall(*args,**kwargs)
    print(f"flushall success, result: {result}")
def test_flushdb(*args,**kwargs):
    r = RedisCacheService()
    result = r.flushdb(*args,**kwargs)
    print(f"flushdb success, result: {result}")

def test_redis_cache_set():
    r = RedisCacheService()
    data = get_random_data()
    if data is None:
        print("create random data failed")
        return
    results = []
    for key, value in data.items():
        results.append(r.set(key, value))
    for result in as_completed(results):
        print(f"set {result.result()} success", end="\r")
    print('\n')
    print(f"set {len(data.keys())} data success")

def test_flush_time():
    print('set redis cache please wait...')
    test_redis_cache_set()
    print('data is ready')
    with benchmark_time('test_flushall'):
        test_flushall()
    print('set redis cache please wait...')
    test_redis_cache_set()
    print('data is ready')
    with benchmark_time('test_flushdb'):
        test_flushdb()
    print('set redis cache please wait...')
    test_redis_cache_set()
    print('data is ready')
    with benchmark_time('test_flushall synchronous'):
        test_flushall(asynchronous=True)
    print('data is ready')
    test_redis_cache_set()
    print('set redis cache please wait...')
    with benchmark_time('test_flushdb synchronous'):
        test_flushdb(asynchronous=True)



if __name__ == '__main__':
    # test_flushdb(asynchronous=True)
    # test_flushall()
    # with benchmark_time('test_redis_cache_set'):
    #     test_redis_cache_set()
    # with benchmark_time('test_get_after_redis_restart'):
    #     test_get_after_redis_restart()
    # with benchmark_time('test_set_and_get_multi_thread'):
    #     test_set_and_get_multi_thread()
    test_flush_time()