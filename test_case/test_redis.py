
import random
import pathlib
import json
from redis import Redis
import timeit



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

def set_random_data(r: Redis, data: dict[str, str]):
    print(f'set {len(data.keys())} data start')
    pipe=r.pipeline()
    for key, value in data.items():
        pipe.set(key, value)
        print(f'set {key} {value} success', end='\r')
    pipe.execute()
    print(f'set {len(data.keys())} data end')
    for key, value in data.items():
        if r.get(key) != value:
            raise Exception(f'set {key} {value} failed')
        print(f'get {key} {value} success', end='\r')
    print(f'set {len(data)} data success')

def test_set_random_data():
    r = Redis(host='host.docker.internal', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print('create random data failed')
        return
    set_random_data(r, data)

def test_redis_is_append():
    r = Redis(host='host.docker.internal', port=6379, db=0, decode_responses=True)
    data = get_random_data()
    if data is None:
        print('create random data failed')
        return
    for key, value in data.items():
        if r.get(key) != value:
            raise Exception(f'append {key} {value} failed')
        print(f'get {key} {value} success', end='\r')
    print(f'append {len(data.keys())} data success')

if __name__ == '__main__':
    create_random_data()
    t = timeit.timeit(test_set_random_data, number=1)
    print(f'test_set_random_data time: {t} seconds')
    # t = timeit.timeit(test_redis_is_append, number=1)
    # print(f'test_redis_is_append time: {t} seconds')