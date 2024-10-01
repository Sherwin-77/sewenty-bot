import datetime
import calendar
from typing import Optional

def add_months(date: datetime.datetime, months: int, reset_day: Optional[int] = None) -> datetime.datetime:
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1
    day = min(reset_day or date.day, calendar.monthrange(year, month)[1])

    return date.replace(year=year, month=month, day=day)