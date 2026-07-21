import abc
import datetime


class DateTimeProvider(abc.ABC):


    @abc.abstractmethod
    def now_as_local(self) -> datetime.datetime:
        pass


    @abc.abstractmethod
    def now_as_utc(self) -> datetime.datetime:
        pass
