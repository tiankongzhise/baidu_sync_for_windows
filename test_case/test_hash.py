from sqlalchemy import create_engine,text
from sqlalchemy.orm import Session
from baidu_sync_for_windows.config import get_config
from baidu_sync_for_windows.dtos import HashDTO
from baidu_sync_for_windows.repository import get_default_repository
from baidu_sync_for_windows.service.hash import hash_service
def create_default_repository():
    config = get_config()
    database = config.database.database_config.database
    connector = config.database.database_config.connector
    user = config.database.database_secret_info.db_user.get_secret_value()
    password = config.database.database_secret_info.db_password.get_secret_value()
    host = config.database.database_secret_info.db_host.get_secret_value()
    port = config.database.database_secret_info.db_port
    name = 'object_backup_test'
    engine_url = f"{database}+{connector}://{user}:{password}@{host}:{port}/{name}"
    engine_params = config.database.database_config.model_dump()
    engine_params.pop("database")
    engine_params.pop("connector")
    engine = create_engine(engine_url,**engine_params)
    return engine
def get_branch_hash_data():
    with Session(create_default_repository()) as session:
        result = session.execute(text("SELECT * FROM backup_record"))
        result_dict = {}
        for row in result.mappings().fetchall():
            result_dict[row['target_object_path']] = {'md5':row['md5'],'sha1':row['sha1'],'sha256':row['sha256'],'fast_hash':row['fast_hash']}
        return result_dict

def is_equal(hash_data:dict[str,str | None],branch_hash_data:dict[str,dict[str,str | None]]) -> bool:
    assert hash_data['md5'].upper() == branch_hash_data[hash_data['target_object_path']]['md5'].upper()
    assert hash_data['sha1'].upper() == branch_hash_data[hash_data['target_object_path']]['sha1'].upper()
    assert hash_data['sha256'].upper() == branch_hash_data[hash_data['target_object_path']]['sha256'].upper()
    assert all([hash_data['fast_hash'] is None,branch_hash_data[hash_data['target_object_path']]['fast_hash'] is None])
    return True
def get_verify_sourec_data():
    repository = get_default_repository()
    with Session(repository.engine) as session:
        result = session.execute(text("SELECT * FROM source_record where target_object_path like 'D:/测试AI运行/%'"))
        result_dict = {}
        for row in result.mappings().fetchall():
            result_dict[row['target_object_path']] = row['id']
        return result_dict
def dto_to_dict(dto:HashDTO,target_object_path:str) -> dict[str,str | None]:
    return {
        'target_object_path':target_object_path,
        'md5':dto.md5,
        'sha1':dto.sha1,
        'sha256':dto.sha256,
        'fast_hash':dto.fast_hash
    }
def get_verify_data():
    branch_hash_data = get_branch_hash_data()
    verify_sourec_data = get_verify_sourec_data()
    print(verify_sourec_data)
    for target_object_path,source_id in verify_sourec_data.items():
        index,hash_data = hash_service(source_id)
        if hash_data is None:
            print(f'hash data is None for source id: {source_id}')
            continue
        compare_data = dto_to_dict(hash_data,target_object_path)
        if target_object_path not in branch_hash_data:
            print(f"verify {target_object_path} failed, not in branch hash data")
            continue
        if is_equal(compare_data,branch_hash_data):
            print(f"verify {target_object_path} success")
        else:
            print(f"verify {target_object_path} failed")

if __name__ == "__main__":
    get_verify_data()
