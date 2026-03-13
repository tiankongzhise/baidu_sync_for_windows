from .base import ServiceException
class SchedulerServiceException(ServiceException):
    pass
class DiskSpaceCoordinatorServiceException(SchedulerServiceException):
    pass