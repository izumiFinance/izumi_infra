# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

PYTHON_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
PYTHON_DATE_FORMAT = "%Y-%m-%d"

def dayRange(start_date: datetime, end_date: datetime):
    """
    day between [start_date, end_date)
    """
    min_date = min(start_date, end_date)
    days = abs(int((end_date - start_date).days))
    for n in range(days):
        yield min_date + timedelta(n)

def hourRange(start_time: datetime, end_time: datetime):
    """
    hour time between [start_time, end_time)
    """
    min_time = min(start_time, end_time)
    hours = abs(int((end_time - start_time).total_seconds() // 3600))
    for n in range(hours):
        yield min_time + timedelta(hours=n)


def left_open_round_number(n: int, r: int) -> int:
    rr = n % r
    if rr == 0: return n - r
    return n // r * r

def right_close_round_number(n: int, r: int) -> int:
    rr = n % r
    if rr == 0: return n
    return ((n // r )+ 1) * r

def get_interval_round_time_range(start_time: datetime, end_time: datetime, delta: timedelta):
    """
    min day
    time between [start_time, end_time) and time % delta == 0

    start = datetime.strptime("2022-11-01 00:00:00", PYTHON_DATETIME_FORMAT)
    end = datetime.strptime("2022-11-03 00:00:00", PYTHON_DATETIME_FORMAT)
    list(get_interval_round_time_range(start, end,timedelta(days=2)))
    """
    timezone_secs = time.timezone
    delta_seconds = int(delta.total_seconds())
    start_round_timestamp = right_close_round_number(int(start_time.timestamp()) - timezone_secs, delta_seconds) + timezone_secs
    end_round_timestamp = left_open_round_number(int(end_time.timestamp()) - timezone_secs, delta_seconds) + timezone_secs
    n = (end_round_timestamp - start_round_timestamp) // delta_seconds + 1
    for i in range(n):
        yield datetime.fromtimestamp(start_round_timestamp + i * delta_seconds)

def get_interval_round_month_range(start_time: datetime, end_time: datetime, delta: relativedelta):
    if delta.months == 1:
        start_time_of_month = start_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_time_of_month = end_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_time_of_month != start_time:
            start_time_of_month = start_time_of_month + delta
        if end_time_of_month == end_time:
            end_time_of_month = end_time_of_month - delta

        while start_time_of_month <= end_time_of_month:
            yield start_time_of_month
            start_time_of_month = start_time_of_month + relativedelta(months=delta.months)

def get_interval_round_week_range(start_time: datetime, end_time: datetime, delta: relativedelta):
    if delta.weeks == 1:
        start_time_week = start_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=start_time.weekday())
        end_time_week = end_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=end_time.weekday())
        if start_time_week != start_time:
            start_time_week = start_time_week + delta
        if end_time_week == end_time:
            end_time_week = end_time_week - delta

        while start_time_week <= end_time_week:
            yield start_time_week
            start_time_week = start_time_week + relativedelta(weeks=delta.weeks)


def get_interval_round_time_list(start_time: datetime, end_time: datetime, delta: timedelta):
    if isinstance(delta, timedelta):
        return list(get_interval_round_time_range(start_time, end_time, delta))
    if isinstance(delta, relativedelta) and delta.months == 1:
        return list(get_interval_round_month_range(start_time, end_time, delta))
    if isinstance(delta, relativedelta) and delta.weeks == 1:
        return list(get_interval_round_week_range(start_time, end_time, delta))
