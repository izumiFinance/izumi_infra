from datetime import datetime, timedelta

PYTHON_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
PYTHON_DATE_FORMAT = "%Y-%m-%d"

def dayRange(start_date: datetime, end_date: datetime):
    """
    day between [start_date, end_date)
    """
    for n in range(abs(int((end_date - start_date).days))):
        yield start_date + timedelta(n)

def hourRange(start_time: datetime, end_time: datetime):
    """
    hour time between [start_time, end_time)
    """
    for n in range(abs(int((end_time - start_time).total_seconds() // 3600))):
        yield end_time + timedelta(hours=n)
