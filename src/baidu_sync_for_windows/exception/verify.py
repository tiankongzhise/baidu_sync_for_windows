from .base import ServiceException
class VerifyServiceException(ServiceException):
    pass
class EncryptNameVerifyServiceException(VerifyServiceException):
    pass