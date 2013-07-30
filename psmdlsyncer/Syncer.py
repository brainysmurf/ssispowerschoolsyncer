from utils.Pandas import PandasDataFrame
import pandas as pd
import numpy as np
import re
import datetime

def num_years(begin, end=None):
    if end is None:
        end = datetime.datetime.now()
    return (end - begin).days / 365.25

def get_years_since_enrolled(enrolment_date):
    return num_years(enrolment_date)

def get_this_academic_year():
    now = datetime.date.today()
    year, month = int(str(now.year)[2:]), now.month
    academic_year = year if month < 8 else year + 1
    return academic_year

def get_year_of_graduation(grade):
    if pd.isnull(grade):
        return grade
    this_year = get_this_academic_year()
    years_left = 12 - int(grade)
    return this_year + years_left

def determine_grade(x):
    if pd.isnull(x) or not x:
        return np.nan
    result = re.sub('[A-Z]', '', x.upper())
    if not result:
        return -1
    else:
        return int(result)

def determine_username(x):
    default_return = ""
    if pd.isnull(x):
        return default_return
    if x:
        where_at = x.index('@')
        if not where_at:
            return default_return
        return x[:where_at].lower()
    else:
        return default_return

def determine_section(grade):
    default = "Undefined Section"
    lowerelem = "Lower Elementary"
    upperelem = "Upper Elementary"
    middleschool = "Middle School"
    highschool = "High School"
    return {1:lowerelem,
            2:lowerelem,
            3:lowerelem,
            4:upperelem,
            5:upperelem,
            6:middleschool,
            7:middleschool,
            8:middleschool,
            9:highschool,
            10:highschool,
            11:highschool,
            12:highschool}.get(grade, default)

def determine_first_and_last(lastfirst):
    split = lastfirst.split(',')
    if not len(split) == 2:
        pass
    last = split[0]
    first = " ".join(split[1:])
    last = last.strip()
    first = first.replace(',', ' ').strip().replace('  ', ' ')
    return first, last

def determine_grade_from_course(course):
    if not course:
        return np.nan
    i = re.sub('[A-Za-z_]', '', course).strip('0')
    # Some courses have 00 on the end
    # TODO: Figure out what that means!
    if not i:
        return np.nan
    return int(i.strip('0'))

from utils.Utilities import no_whitespace_all_lower    
NAMESPLIT = ', '

def derive_username(index, row):
    if pd.isnull(row['graduation']):
        #TODO Figure out a way to scan in iterrows that excludes nan objects?
        # It's annoying to have to check for this in every function
        return ""
    return "{}{}".format(no_whitespace_all_lower(row['name'])[:20], int(row['graduation']))


def derive_fullname(name):
    split = name.split(', ')
    return "{} {}".format(split[1], split[0])

def determine_grade_from_coursename(name):
    if not name:
        return np.nan
    result = re.search(r'\(([0-9]+)\)', name)
    if not result:
        return np.nan
    return int(result.group(1))

import sys
from io import StringIO
import contextlib

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

def deserialize(obj):
    with stdoutIO() as code:
        exec("print(" + obj + ")")
    return code.getvalue()

def serialize(obj):
    return str(obj)

if __name__ == "__main__":

    students = PandasDataFrame.from_csv('../powerschool/ssis_studentinfo_v2.1',
                                        header=None,
                                        names=["powerschoolID", "id", "homeroom","fullname","emails","entrydate","nationality","delete"],
                                        converters={5:pd.to_datetime})
    staff = PandasDataFrame.from_csv('../powerschool/ssis_teacherinfodumpall',
                                        header=None,
                                        names=["fullname", "email", "title", "school", "something"],
                                        index_col=0)
    schedule = PandasDataFrame.from_csv('../powerschool/ssis_studentscheduledumpsec',
                                        header=None,
                                        names=["course","period", "termid", "teacher","studentname", "studentid"],
                                        index_col=False)
    allocations = PandasDataFrame.from_csv('../powerschool/ssis_teacherallocationsec',
                                           header=None,
                                           names=["coursecode", "coursename", "teachername", "termid", "delete"],
                                           index_col=False)
    
    students.assign_column('grade',         from_column={'homeroom': determine_grade})
    students.assign_column('emails',         from_column={'emails': lambda x: x.lower()})  # how bad is this?
    students.assign_column('section',       from_column={'grade':determine_section})
    students.assign_column('first',         to=students.split_column_text('fullname', NAMESPLIT, 1))
    students.assign_column('last',          to=students.split_column_text('fullname', NAMESPLIT, 0))
    students.assign_column('name',          by_iterrows=lambda index, row: row['first'] + ' ' + row['last'])
    students.assign_column('graduation',    from_column={'grade':get_year_of_graduation})
    students.assign_column('orig_username', by_iterrows=derive_username)

    #TODO: Fill in username by checking DragonNet first
    students.assign_column('username',      from_column={'orig_username':lambda x: x})

    students.assign_column('yearsenrolled', from_column={'entrydate':get_years_since_enrolled})
    students.assign_column('parentID',      from_index=lambda x: str(x)[:4]+'P')

    staff.set_column_nas('email',           value="")
    staff.set_column_nas('title',           value="")
    staff.assign_column('username',         from_column={'email':determine_username})
    staff.assign_column('account_type',     to="Teacher")

    #TODO: Change this to "teacherID" when I have it!
    schedule.assign_column('teacherID',     from_column={'teacher':lambda teacher: staff.row_column(teacher, 'username')})
    schedule.assign_column('teacherusername',
                           from_column={'teacher':lambda teacher: staff.row_column(teacher, 'username')})

    students.assign_column('teachers',      to=schedule.change_index('studentid').collapse_multiple_values('teacherID'))
    students.set_column_nas('teachers',     value="")

    schedule.assign_column('class',         by_iterrows=lambda index, row: row['teacherusername'] + row['course'])
    students.assign_column('classes',       to=students.collapse_foreign_column(schedule, 'studentid'))

    allocations.assign_column('grade',      from_column={'coursename':determine_grade_from_coursename})

    from IPython import embed
    embed()


    #from utils.FilesFolders import clear_folder

    #exclude_db_files = lambda x: x.endswith('.db')
    #path = '../postfix2'
    #clear_folder(path, exclude=exclude_db_files)

    #for grade in students.dataframe['grade'].unique:
        
    
