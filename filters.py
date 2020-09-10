from datetime import date, datetime, timedelta


def filter_day(dt):
    if isinstance(dt, datetime):
        dt = dt.date()
    if dt == date.today():
        return "Heute"
    elif dt == date.today() - timedelta(days=1):
        return "Gestern"
    else:
        return dt.strftime("%d.%m.%Y")


def filter_time(dt):
    return dt.strftime("%H:%M")
