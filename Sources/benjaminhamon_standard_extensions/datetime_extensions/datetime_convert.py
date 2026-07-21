import datetime
import re
from typing import Dict, List


def convert_timedelta_from_string(value_as_string: str) -> datetime.timedelta:
    element_collection = value_as_string.split(" ")

    element_regex = re.compile(r"^(?P<value>[0-9]+)(?P<unit>w|d|h|m|s|ms|μs)$")

    unit_collection = [
        ("w", "weeks"),
        ("d", "days"),
        ("h", "hours"),
        ("m", "minutes"),
        ("s", "seconds"),
        ("ms", "milliseconds"),
        ("μs", "microseconds"),
    ]

    timedelta_arguments: Dict[str,int] = {}
    last_unit_index = -1

    for element in element_collection:
        element_match = element_regex.search(element)
        if element_match is None:
            raise ValueError("invalid value: '%s'" % value_as_string)

        unit = next(x for x in unit_collection if x[0] == element_match.group("unit"))

        unit_index = unit_collection.index(unit)
        if last_unit_index >= unit_index:
            raise ValueError("invalid value: '%s'" % value_as_string)
        last_unit_index = unit_index

        timedelta_arguments[unit[1]] = int(element_match.group("value"))

    return datetime.timedelta(**timedelta_arguments)


def convert_timedelta_to_string(value: datetime.timedelta) -> str:
    element_collection: List[str] = []

    if value.total_seconds() < 0:
        raise ValueError("negative values are not supported")

    if value.days > 0:
        element_collection.append(str(value.days) + "d")

    if value.seconds > 0:
        remainder = value.seconds

        hours, remainder = divmod(remainder, 3600)
        if hours > 0:
            element_collection.append(str(hours) + "h")

        minutes, remainder = divmod(remainder, 60)
        if minutes > 0:
            element_collection.append(str(minutes) + "m")

        seconds = remainder
        if seconds > 0:
            element_collection.append(str(seconds) + "s")

    if value.microseconds > 0:
        remainder = value.microseconds

        milliseconds, remainder = divmod(remainder, 1000)
        if milliseconds > 0:
            element_collection.append(str(milliseconds) + "ms")

        microseconds = remainder
        if microseconds > 0:
            element_collection.append(str(microseconds) + "μs")

    if len(element_collection) == 0:
        return "0s"

    return " ".join(element_collection)
