from sqlalchemy import create_engine
from baidu_sync_for_windows.config import get_config
from .interface import MysqlRepository
DefaultRepository = MysqlRepository
def create_default_repository()->MysqlRepository:
    config = get_config()
    database = config.database.database_config.database 
    connector = config.database.database_config.connector
    user = config.database.database_secret_info.db_user.get_secret_value()
    password = config.database.database_secret_info.db_password.get_secret_value()
    host = config.database.database_secret_info.db_host.get_secret_value()
    port = config.database.database_secret_info.db_port
    name = config.database.database_secret_info.db_name.get_secret_value()
    engine_url = f"{database}+{connector}://{user}:{password}@{host}:{port}/{name}"
    engine_params = config.database.database_config.model_dump()
    engine_params.pop("database")
    engine_params.pop("connector")
    repository = MysqlRepository(engine=create_engine(engine_url,**engine_params))
    repository.create_tables()
    return repository

default_repository = None
def get_default_repository()->MysqlRepository:
    global default_repository
    if default_repository is None:
        default_repository = create_default_repository()
    return default_repository