import datetime
import time

def time_now():
    return int(time.time())

def yearsago(years, from_date=None):
    if from_date is None:
        from_date = datetime.datetime.now()
    try:
        return from_date.replace(year=from_date.year - years)
    except:
        # Must be 2/29!
        assert from_date.month == 2 and from_date.day == 29 # can be removed
        return from_date.replace(month=2, day=28,
                                 year=from_date.year-years)

def num_years(begin, end=None):
    if end is None:
        end = datetime.datetime.now()
    return (end - begin).days / 365.25

def get_years_since_enrolled(enrolment_date):
    return num_years(enrolment_date)

def get_academic_start_date():
    now = datetime.date.today()
    year = now.year if now.month in range(8, 13) else now.year - 1
    return datetime.datetime(2013, 8, 1)

def get_this_academic_year():
    now = datetime.date.today()
    year, month = int(str(now.year)[2:]), now.month
    academic_year = year if month < 8 else year + 1
    return academic_year

def get_year_of_graduation(grade):
    this_year = get_this_academic_year()
    years_left = 12 - int(grade)
    return this_year + years_left

def date_to_database_timestamp(year=None, month=None, day=None):
    """
    Converts day to the kind of timestamp used by moodle's database module
    It uses hour=12 as default, and strips the decimal
    """
    return int((datetime.datetime(year=year, month=month, day=day, hour=12) - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds=1))

def timestamp_to_python_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)

def today():
    return datetime.date.today()

def tomorrow():
    return today() + datetime.timedelta(days=1)

def day_after_tomorrow():
    return today() + datetime.timedelta(days=2)

def day_n_after_today(n):
    return today() + datetime.timedelta(days=n)

def yesterday():
    return today() - datetime.timedelta(days=1)

# Following gives me 1st, 2nd, 3rd, 4th, etc
def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


if __name__ == "__main__":

    print(get_year_of_graduation(10))
    print(get_year_of_graduation(7))
    print(get_year_of_graduation(12))
