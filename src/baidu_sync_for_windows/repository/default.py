from .mysql import DefaultRepository as MysqlDefaultRepository,get_default_repository as get_mysql_default_repository

DefaultRepository = MysqlDefaultRepository
def get_default_repository()->DefaultRepository:
    return get_mysql_default_repository()
