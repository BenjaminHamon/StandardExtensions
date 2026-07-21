import datetime

import pytest

from benjaminhamon_standard_extensions.datetime_extensions import datetime_convert


def test_convert_timedelta_from_string_with_simple_value() -> None:
    timedelta = datetime_convert.convert_timedelta_from_string("1d 5m")
    assert timedelta == datetime.timedelta(days = 1, minutes = 5)


def test_convert_timedelta_from_string_with_all_units() -> None:
    timedelta = datetime_convert.convert_timedelta_from_string("1w 2d 3h 4m 5s 6ms 7μs")
    assert timedelta == datetime.timedelta(weeks = 1, days = 2, hours = 3, minutes = 4, seconds = 5, milliseconds = 6, microseconds = 7)


def test_convert_timedelta_from_string_with_wrong_order() -> None:
    with pytest.raises(ValueError):
        datetime_convert.convert_timedelta_from_string("5m 1d")


def test_convert_timedelta_from_string_with_wrong_unit() -> None:
    with pytest.raises(ValueError):
        datetime_convert.convert_timedelta_from_string("1x 5m")


def test_convert_timedelta_from_string_with_duplicate_unit() -> None:
    with pytest.raises(ValueError):
        datetime_convert.convert_timedelta_from_string("1m 5m")


def test_convert_timedelta_from_string_with_missing_unit() -> None:
    with pytest.raises(ValueError):
        datetime_convert.convert_timedelta_from_string("1 5m")


def test_convert_timedelta_to_string_with_simple_value() -> None:
    timedelta_as_string = datetime_convert.convert_timedelta_to_string(datetime.timedelta(days = 1, minutes = 5))
    assert timedelta_as_string == "1d 5m"


def test_convert_timedelta_to_string_with_all_units() -> None:
    timedelta_as_string = datetime_convert.convert_timedelta_to_string(
        datetime.timedelta(weeks = 1, days = 2, hours = 3, minutes = 4, seconds = 5, milliseconds = 6, microseconds = 7))

    assert timedelta_as_string == "9d 3h 4m 5s 6ms 7μs"
