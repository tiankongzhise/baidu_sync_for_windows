from .base import ServiceException
class CompressServiceException(ServiceException):
    pass
class EncryptNameCompressServiceException(CompressServiceException):
    pass