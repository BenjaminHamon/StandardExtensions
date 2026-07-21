import datetime

from benjaminhamon_standard_extensions.datetime_extensions.datetime_provider import DateTimeProvider


class DateTimeProviderImplementation(DateTimeProvider):


    def now_as_local(self) -> datetime.datetime:
        return datetime.datetime.now()


    def now_as_utc(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)
