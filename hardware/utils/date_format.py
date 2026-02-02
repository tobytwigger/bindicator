import datetime

def format_date(date):
    # If date is today, return 'Today'
    if date == datetime.date.today():
        return 'Today'

    # If date is tomorrow, return 'Tomorrow'
    if date == datetime.date.today() + datetime.timedelta(days=1):
        return 'Tomorrow'

    # Otherwise, return the date in the format 'Mon, 01 Jan'
    return date.strftime('%a, %d %b')