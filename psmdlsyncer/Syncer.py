from utils.Pandas import PandasDataFrame
import pandas as pd
import numpy as np
import re
import datetime

from psmdlsyncer.settings import config, requires_setting, flag_passed
from psmdlsyncer.ModifyDragonNet import DragonNetModifier
from psmdlsyncer.utils.DB import DragonNetDBConnection

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

def determine_grade_from_coursename(coursename):
    m = re.search(r'\(([0-9]+)\)$', coursename)
    if not m:
        return 0
    return m.group(1)

def determine_grade(x):
    if pd.isnull(x) or not x:
        return np.nan
    result = re.sub('[A-Z]', '', x.upper())
    if not result:
        return -1
    else:
        return int(result) + 1 # FIXME: CHANGE THIS WHEN POWERSCHOOL'S SCHEDULE HAS BEEN UPDATED

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

def determine_username_from_email(username):
    if not username or pd.isnull(username):
        return ""
    if "@" not in username:
        return ""
    return username[:username.index('@')]

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

def wrap_row_to_object(row):
    obj = lambda x: None
    for column in row.index.tolist():
        setattr(obj, column, row[column])
    return obj

def sync_dragonnet_accounts(staff_database):
    """
    If DragoNet doesn't have any accounts listed, creates them
    Composes and sends email to them letting them know
    """
    from psmdlsyncer.utils.DB import DragonNetDBConnection
    dn = DragonNetDBConnection()    
    from_dn = PandasDataFrame(dn.sql(
        'select idnumber, username, firstname, lastname, email from ssismdl_user where deleted = 0'
        )(), columns=["powerschoolID", "username", "first_name", "last_name", "email"])
    
    #current_staff = PandasDataFrame.from_dataframe(staff_database.dataframe[staff_database.dataframe['status'] == 1 & staff_database.dataframe['staff_status'] == 2].
    #                                               set_index('username').sort_index())

    dn_list = from_dn.new_index('username').dataframe.index.tolist()
    sdf = staff_database.dataframe
    support_staff_to_add = sdf[ (sdf.email.str.len>0) & (sdf.status == 1) & (sdf.staff_status == 2) & (-sdf.username.isin(dn_list))]
    teaching_staff_to_add = sdf[ (sdf.email.str.len>0) & (sdf.status == 1) & (sdf.staff_status == 1) & (-sdf.username.isin(dn_list)) ]
    staff_to_delete = sdf[ (sdf.email.str.len>0) & (sdf.status == 2) & (sdf.username.isin(dn_list)) ]

def update_this_time(staff):
    """ throwaway at the beginning of the year """
    from_excel = PandasDataFrame.from_excel('/Users/brainysmurf/Downloads/Secondary Teachers 2013-14.xls', 'Sheet1', index_col=None, na_values=['NA'])
    from_excel.assign_column('full_name', by_iterrows=lambda index, row: row['Given Name'].strip() + ' ' + row['Family Name'].strip())
    

def sync_sec_students_enrollments(students, courses, schedule):
    """
    PARSES schedule AND QUERIES DRAGONNET, UPDATING DRAGONNET TO MATCH declared_enrollments
    """
    dn = DragonNetDBConnection()
    mod_dn = DragonNetModifier()
    queried_enrollments = PandasDataFrame(dn.get_all_users_enrollments(), columns=['powerschoolID', 'group', 'course'], index=None)
    from IPython import embed
    embed()


    # DEFINE declared_enrollments
    #TODO: Insert course and group mapping code here... pain in the ass!
    declared_cohorts = PandasDataFrame({'powerschoolID':students.dataframe['powerschoolID'].tolist()})
    
def sync_support_staff_cohorts(staff):
    """
    I'M NOT GOING TO DO THIS UNTIL DREW TELLS HIS STAFF TO GIVE PROPER POWERSCHOOL IDs TO EVERYONE
    """
    staff_IDs = staff.dataframe[ staff.dataframe['is_secondary'] ]['powerschoolID'].values.tolist()
    dn = DragonNetDBConnection()
    mod_dn = DragonNetModifier()
    queried_cohorts = PandasDataFrame(dn.get_user_cohort_enrollments(), columns=['powerschoolID', 'cohort'], index=None)
    queried_cohorts.pivot_table(rows='powerschoolID', cols='cohort', aggfunc=lambda x: True, fill_value=False)    

    # DEFINE declared_enrollments

    # BECAUSE COHORTS HAVE TO BE CREATED IN DRAGONNET,
    # CHECK FOR THAT SITUATION WHERE WE HAVE COHORTS DECLARED BUT DON'T ACTUALLY
    # EXIST IN THE SYSTEM YET
    # TODO: Present some sort of warning, or something
    declared_names = ['supportstaffALL']
    queried_names = queried_cohorts.dataframe.columns.tolist()
    for missing_enrollment in set(declared_names) - set(queried_names):
        queried_cohorts.assign_column(missing_enrollment, to=False)

    # PROGRAMATICALLY SET UP declared_names
    declared_cohorts = PandasDataFrame({'powerschoolID':staff.dataframe['powerschoolID'].tolist()})
    from IPython import embed
    embed()
    staff.change_index('powerschoolID')  # THIS REALLY IS NEEDED FOR BELOW STATEMENTS TO WORK
    declared_cohorts.assign_column('studentsALL', to=True)
    declared_cohorts.change_index('powerschoolID')  # do I need this?

    # FILTER OUT BOTH QUERIED AND DECLARED FOR SECONDARY ONLY
    temp = queried_cohorts.dataframe.reset_index()
    temp = temp[ temp['powerschoolID'].isin(staff_IDs) ]
    staff_queried_cohorts = PandasDataFrame.from_dataframe(temp)
    temp = declared_cohorts.dataframe.reset_index()
    temp = temp[ temp['powerschoolID'].isin(staff_IDs) ]
    staff_declared_cohorts = PandasDataFrame.from_dataframe(temp)
    
    staff_queried_cohorts.change_index('powerschoolID')
    staff_declared_cohorts.change_index('powerschoolID')
    
    # GO THROUGH EACH ITEM
    # item.index   = powerschoolID
    # item.column  = cohort
    # item.left    = VALUE IT SHOULD BE (DEFINED IN secondary_declared_cohorts
    # item.right   = VALUE IT WAS FOUND (DEFINED IN secondary_queried_cohorts
    for item in staff_declared_cohorts.identify_differences \
            (staff_queried_cohorts.set_columns(*declared_names)):
        if item.is_deleted:
            pass
        elif item.is_new:
            pass
        # TODO: MAKE should AND should_not OR SOMETHING
        else:
            if item.left:
                # SHOULD BE IN THERE, BUT ISN'T
                mod_dn.add_user_to_cohort(item.index, item.column)
            elif item.right:
                # SHOULD NOT BE IN THERE, AND IS
                mod_dn.remove_user_from_cohort(item.index, item.column)


def sync_sec_students_cohorts(students):
    """
    PARSES students AND QUERIES DRAGONNET, UPDATING DRAGONNET TO MATCH declared_cohorts
    """
    secondary_student_IDs = students.dataframe[ students.dataframe['is_secondary'] ]['powerschoolID'].values.tolist()
    # DEFINE queried_cohorts
    # QUERY DRAGONNET USING get_user_cohort_enrollments FOR EXISTING ENROLLMENTS
    # SO USE pivot_table TO FORMAT QUERTY RESULT (userid, cohort) INTO A TRUTH-TABLE
    dn = DragonNetDBConnection()
    mod_dn = DragonNetModifier()
    queried_cohorts = PandasDataFrame(dn.get_user_cohort_enrollments(), columns=['powerschoolID', 'cohort'], index=None)
    queried_cohorts.pivot_table(rows='powerschoolID', cols='cohort', aggfunc=lambda x: True, fill_value=False)

    # DEFINE declared_names

    # BECAUSE COHORTS HAVE TO BE CREATED IN DRAGONNET,
    # CHECK FOR THAT SITUATION WHERE WE HAVE COHORTS DECLARED BUT DON'T ACTUALLY
    # EXIST IN THE SYSTEM YET
    # TODO: Present some sort of warning, or something
    declared_names = ['studentsALL', 'studentsSEC', 'studentsMS', 'studentsHS']
    queried_names = queried_cohorts.dataframe.columns.tolist()
    for missing_enrollment in set(declared_names) - set(queried_names):
        queried_cohorts.assign_column(missing_enrollment, to=False)

    # PROGRAMATICALLY SET UP declared_names
    declared_cohorts = PandasDataFrame({'powerschoolID':students.dataframe['powerschoolID'].tolist()})
    students.change_index('powerschoolID')  # THIS REALLY IS NEEDED FOR BELOW STATEMENTS TO WORK
    declared_cohorts.assign_column('studentsALL', to=True)
    declared_cohorts.change_index('powerschoolID')  # otherwise, students.filter will get wrong results
    declared_cohorts.assign_column('studentsSEC', to=students.filter(column='grade', by_list=range(6, 14)))  #FIXME: CHANGE BACK TO 13
    declared_cohorts.assign_column('studentsMS',  to=students.filter(column='grade', by_list=range(6, 9)))
    declared_cohorts.assign_column('studentsHS',  to=students.filter(column='grade', by_list=range(9, 14)))  #FIXME: CHANGE BACK TO 13

    # FILTER OUT BOTH QUERIED AND DECLARED FOR SECONDARY ONLY
    temp = queried_cohorts.dataframe.reset_index()
    temp = temp[ temp['powerschoolID'].isin(secondary_student_IDs) ]
    secondary_queried_cohorts = PandasDataFrame.from_dataframe(temp)
    temp = declared_cohorts.dataframe.reset_index()
    temp = temp[ temp['powerschoolID'].isin(secondary_student_IDs) ]
    secondary_declared_cohorts = PandasDataFrame.from_dataframe(temp)
    
    secondary_queried_cohorts.change_index('powerschoolID')
    secondary_declared_cohorts.change_index('powerschoolID')
    
    # GO THROUGH EACH ITEM
    # item.index   = powerschoolID
    # item.column  = cohort
    # item.left    = VALUE IT SHOULD BE (DEFINED IN secondary_declared_cohorts
    # item.right   = VALUE IT WAS FOUND (DEFINED IN secondary_queried_cohorts
    for item in secondary_declared_cohorts.identify_differences \
            (secondary_queried_cohorts.set_columns(*declared_names)):
        if item.is_deleted:
            pass
        elif item.is_new:
            pass
        # TODO: MAKE should AND should_not OR SOMETHING
        else:
            if item.left:
                # SHOULD BE IN THERE, BUT ISN'T
                mod_dn.add_user_to_cohort(item.index, item.column)
            elif item.right:
                # SHOULD NOT BE IN THERE, AND IS
                mod_dn.remove_user_from_cohort(item.index, item.column)

if __name__ == "__main__":

    requires_setting('DIRECTORIES', 'path_to_powerschool_dump')
    full_path = lambda _file: config['DIRECTORIES'].get('path_to_powerschool_dump') + '/' + _file

    # TODO: MAKE SURE THEY GET THE LATEST VERSION AUTOMAGICALLY?
    # TODO: FIGURE OUT A WAY TO GET THE HEADERS IN POWERSCHOOL FILE
    students = PandasDataFrame.from_csv(full_path('ssis_dist_studentinfo_v3.0'),
                                        header=None,
                                        names=["powerschoolID", "id",
                                               "homeroom", "fullname", "emails", "entrydate", "nationality", "delete"],
                                        dtype={'powerschoolID':np.object},
                                        index_col=False,
                                        converters={5:pd.to_datetime})
    staff = PandasDataFrame.from_csv(full_path('ssis_dist_staffinfo_v2.0'),
                                     header=None,
                                     names=["powerschoolID",
                                            "first_name", "preferred_name", "middle_name", "last_name",
                                            "email", "title", "staff_status", "status", "delete"],
                                     index_col=None,
                                     dtype={'powerschoolID':np.object})

    schedule = PandasDataFrame.from_csv(full_path('ssis_sec_studentschedule_v3.0'),
                                        header=None,
                                        names=["course","period", "termid",
                                               "teacher","studentname", "studentid"],
                                        index_col=False)
    courses = PandasDataFrame.from_csv(full_path('ssis_sec_courseinfo'),
                                       header=None,
                                       names=["course", "name"],
                                       index_col=False)
    allocations = PandasDataFrame.from_csv(full_path('ssis_teacherallocationsec'),
                                           header=None,
                                           names=["coursecode", "coursename",
                                                  "teachername", "termid", "delete"],
                                           index_col=False)

    # setup courses with schedule
    courses.assign_column('grade',         from_column={'name':determine_grade_from_coursename})
    
    # set up staff tables
    staff.set_column_nas('email',           value="")
    staff.set_column_nas('title',           value="")
    staff.assign_column('username',         from_column={'email':determine_username})
    staff.assign_column('left',             to=staff.dataframe['status']==2)
    staff.assign_column('still_here',       to=staff.dataframe['status']==1)
    staff.set_column_nas('username',        value="")
    staff.assign_column('account_type',     to="Teacher")
    staff.assign_column('is_support_staff', to=staff.dataframe['staff_status']==2)
    staff.assign_column('is_secondary',     to=staff.dataframe['staff_status']==1)
    staff.assign_column('is_elementary',    to=staff.dataframe['staff_status']==0)

    # set up schedule
    

    # set up students
    students.assign_column('grade',         from_column={'homeroom': determine_grade})
    students.assign_column('emails',        from_column={'emails': lambda x: x.lower()})  # how bad is this?
    students.assign_column('section',       from_column={'grade':determine_section})
    students.assign_column('first',         to=students.split_column_text('fullname', NAMESPLIT, 1))
    students.assign_column('last',          to=students.split_column_text('fullname', NAMESPLIT, 0))
    students.assign_column('name',          by_iterrows=lambda index, row: row['first'] + ' ' + row['last'])
    students.assign_column('graduation',    from_column={'grade':get_year_of_graduation})
    students.assign_column('orig_username', by_iterrows=derive_username)
    students.assign_column('yearsenrolled', from_column={'entrydate':get_years_since_enrolled})
    students.assign_column('parentID',      from_index=lambda x: str(x)[:4]+'P')
    students.assign_column('is_secondary',  from_column={'grade':lambda x: x in range(6, 13)})
    students.assign_column('is_elementary', from_column={'grade':lambda x: x in range(1, 6)})
    students.assign_column('is_highschool',  from_column={'grade':lambda x: x in range(9, 13)})
    students.assign_column('is_middleschool',from_column={'grade':lambda x: x in range(6, 10)})

    allocations.assign_column('grade',      from_column={'coursename':determine_grade_from_coursename})

    if flag_passed('enroll_cohorts'):
        #sync_support_staff_cohorts(staff)    FIXME: POWERSCHOOL IDs HAVE TO WORK FOR EVERYONE THE SAME WAY
        sync_sec_students_cohorts(students)
    if flag_passed('enroll_groups'):
        sync_sec_students_enrollments(students, courses, schedule)

