import datetime
import calendar
from typing import Optional

def add_months(date: datetime.datetime, months: int, reset_day: Optional[int] = None) -> datetime.datetime:
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1
    day = min(reset_day or date.day, calendar.monthrange(year, month)[1])

    return date.replace(year=year, month=month, day=day)


def start_of_day(date: datetime.datetime) -> datetime.datetime:
    return date.replace(hour=0, minute=0, second=0, microsecond=0)

def end_of_day(date: datetime.datetime) -> datetime.datetime:
    return date.replace(hour=23, minute=59, second=59, microsecond=999999)