"""Module providing small useful functions used in the application"""
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta



DATE_FORMAT = '%d/%m/%Y'

def get_today_date() -> datetime:
    """
    Retrieves the current date and time.

    Returns:
        datetime: The current date and time as a datetime object.
    """
    return datetime.now()

def get_future_date(month_quantity: int=6) -> str:
    """Retrieves future data from current local date
    Args:
        month_quantity (int): number of months to be added to current date

    Returns:
        str: current date plus number of months from month_quantity
    """
    current_date = date.today()
    new_date = current_date + relativedelta(months=+month_quantity)
    return new_date.strftime(DATE_FORMAT)

def get_tomorrow_date() -> str:
    """Retrieves tomorrow local date in proper format"""
    tomorrow_date = date.today() + relativedelta(days=+1)
    return tomorrow_date.strftime(DATE_FORMAT)
