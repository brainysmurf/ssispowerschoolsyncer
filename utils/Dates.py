import datetime

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

def today():
    return datetime.date.today()

def tomorrow():
    return today() + datetime.timedelta(days=1)

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
