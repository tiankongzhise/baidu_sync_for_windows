from sqlalchemy import create_engine
from .mysql import MysqlRepository
DefaultRepository = MysqlRepository
def default_repository()->MysqlRepository:
    return MysqlRepository(engine=create_engine("mysql+pymysql://root:123456@localhost:3306/baidu_sync"))

