import datetime


class DateTimeProvider:


    def utcnow(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)
