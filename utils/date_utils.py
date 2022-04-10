from datetime import date, timedelta

def dayrange(start_date, end_date):
    """
    day between [start_date, end_date)
    """
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

PYTHON_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
PYTHON_DATE_FORMAT = "%Y-%m-%d"
