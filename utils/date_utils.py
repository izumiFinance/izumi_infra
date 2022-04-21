from datetime import datetime, timedelta

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
