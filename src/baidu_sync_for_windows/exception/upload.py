from .base import ServiceException
class UploadServiceException(ServiceException):
    pass
class EncryptNameUploadServiceException(UploadServiceException):
    pass