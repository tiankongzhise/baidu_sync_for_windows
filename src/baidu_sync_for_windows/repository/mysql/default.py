from sqlalchemy import create_engine,Engine
from baidu_sync_for_windows.config import get_config
def create_default_engine()->Engine:
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
    return create_engine(engine_url,**engine_params)