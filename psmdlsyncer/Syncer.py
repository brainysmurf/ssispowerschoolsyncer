from IPython import embed
from utils.Pandas import PandasDataFrame
import pandas as pd
import numpy as np
import re
import datetime

from psmdlsyncer.settings import config, requires_setting, flag_passed
from psmdlsyncer.ModifyDragonNet import DragonNetModifier
from psmdlsyncer.utils.DB import DragonNetDBConnection
from collections import defaultdict

from psmdlsyncer.settings import verbose, verbosity

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
    if grade >= 0:
        years_left_in_school = 12 - grade
    else:
        years_left_in_school = 12 + abs(grade)
    return this_year + years_left_in_school

def determine_grade_from_coursename(coursename):
    m = re.search(r'\(([0-9]+)\)$', coursename)
    if not m:
        return 0
    return m.group(1)

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

def identify_differences(left: "PandasDataFrame", right: "PandasDataFrame",
                         leftfunc, rightfunc,
                         notinleftfunc, notinrightfunc):
    """
    More abstract code used for syncing procedures
    """
    embed()
    verbose = verbosity('Sync')
    for item in left.identify_differences(right):
        if item.is_not_in_left:
            if notinleftfunc:
                notinleftfunc(item) 
        elif item.is_not_in_right:
            if notinrightfunc:
                notinrightfunc(item)
        # TODO: MAKE should AND should_not OR SOMETHING
        else:
            if item.left:
                # SHOULD BE IN THERE, BUT ISN'T
                if leftfunc:
                    leftfunc(item)
            elif item.right:
                # SHOULD NOT BE IN THERE, AND IS
                if rightfunc:
                    rightfunc(item)

class Sync:
    """
    Controller for syncing operations
    Model for passed item in constructor are PandasDataFrame objects
    """
    
    def __init__(self, students, staff, parents, schedule, allocations):
        self._dn = None
        self._queried_enrollments = None
        self._query_userid_idnumber = None
        self._qpfd = None
        self._queried_cohorts = None
        self.verbose = verbosity('Sync')
        self.mod_dn = DragonNetModifier()
        self.students = students
        self.staff = staff
        self.parents = parents
        self.schedule = schedule
        self.allocations = allocations

    def add_user_to_cohort(self, item):
        self.verbose and print(" + cohort {:12} {}".format(item.column, self.students.get(item.index, 'str')))
        self.mod_dn.add_user_to_cohort(item.index, item.column)

    def remove_user_from_cohort(self, item):
        self.verbose and print(" - cohort {:12} {}".format(item.column, self.students.get(item.index, 'str')))
        self.mod_dn.remove_user_from_cohort(item.index, item.column)

    def add_profile_for_user(self, item):
        userid = self.get_userid_from_idnumber(item.index)
        print("Adding", userid, item.left)

    def remove_profile_for_user(self, item):
        userid = self.get_userid_from_idnumber(item.index)
        print("Removing", userid, item.left)

    @property
    def get_dn_connection(self):
        if self._dn is None:
            self._dn = DragonNetDBConnection()
        return self._dn

    @property
    def queried_enrollments(self):
        if self._queried_enrollments is None:
            self._queried_enrollments = PandasDataFrame(self.get_dn_connection.get_all_users_enrollments(),
                                                        columns=['powerschoolID', 'group', 'course'])
        return self._queried_enrollments

    @property
    def query_userid_idnumber(self):
        if self._query_userid_idnumber is None:
            self._query_userid_idnumber = PandasDataFrame(self.get_dn_connection.get_userid_idnumber(),
                                                          columns=['userid', 'powerschoolID', 'username'])
            self._query_userid_idnumber.change_index('powerschoolID')
        return self._query_userid_idnumber

    def get_userid_from_idnumber(self, idnumber):
        return self.query_userid_idnumber.row_column(idnumber, 'userid')

    @property
    def queried_profile_field_data(self):
        if self._qpfd is None:
            self._qpfd = PandasDataFrame(self.get_dn_connection.get_user_profile_data(),
                                                               columns=['powerschoolID','userid', 'field', 'value'],
                                                               index=None)
            # DTYPE DOESN'T WORK, SO ADJUST THE VALUES MANUALLY
            self._qpfd.assign_column('value', from_column={'value': lambda x: True if int(x) else False})
            self._qpfd.filter(column='value', equals=True)
            newlist = self._qpfd.columns_list
            value_index = newlist.index('value')
            if not value_index:
                print("won't work!")
            newlist.pop(value_index)

            self._qpfd.dataframe = self._qpfd.dataframe[self._qpfd.dataframe['value']==True]
            self._qpfd = self._qpfd.set_columns(*newlist)

            self._qpfd.pivot_table(rows='powerschoolID',
                                   cols='field',
                                   aggfunc=lambda x: True,
                                   fill_value=False)
            
        return self._qpfd

    @property
    def queried_cohorts(self):
        if self._queried_cohorts is None:
            self._queried_cohorts = PandasDataFrame(self.get_dn_connection.get_user_cohort_enrollments(),
                                                    columns=['powerschoolID', 'cohort'],
                                                    index=None)
            self._queried_cohorts.pivot_table(rows='powerschoolID', cols='cohort', aggfunc=lambda x: True, fill_value=False)    
        return self._queried_cohorts
    
    def sync_dragonnet_accounts(self):
        """
        If DragoNet doesn't have any accounts listed, creates them
        Composes and sends email to them letting them know
        """
        from_dn = PandasDataFrame(dn.sql(
            'select idnumber, username, firstname, lastname, email from ssismdl_user where deleted = 0'
            )(), columns=["powerschoolID", "username", "first_name", "last_name", "email"])

        #current_staff = PandasDataFrame.from_dataframe(staff_database.dataframe[staff_database.dataframe['status'] == 1 & staff_database.dataframe['staff_status'] == 2].
        #                                               set_index('username').sort_index())

        dn_list = from_dn.new_index('username').dataframe.index.tolist()
        sdf = self.staff.dataframe
        support_staff_to_add = sdf[ (sdf.email.str.len>0) & (sdf.status == 1) & (sdf.staff_status == 2) & (-sdf.username.isin(dn_list))]
        teaching_staff_to_add = sdf[ (sdf.email.str.len>0) & (sdf.status == 1) & (sdf.staff_status == 1) & (-sdf.username.isin(dn_list)) ]
        staff_to_delete = sdf[ (sdf.email.str.len>0) & (sdf.status == 2) & (sdf.username.isin(dn_list)) ]

    def sync_sec_students_enrollments(self):
        """
        PARSES schedule AND QUERIES DRAGONNET, UPDATING DRAGONNET TO MATCH declared_enrollments
        """
        #TODO: Do it
        pass

    def sync_teachers(self):
        embed()
        declared_cohorts = PandasDataFrame({'powerschoolID':self.staff.dataframe['powerschoolID'].tolist()})
        
    
    def sync_staff_cohorts(self):
        """
        I'M NOT GOING TO DO THIS UNTIL DREW TELLS HIS STAFF TO GIVE PROPER POWERSCHOOL IDs TO EVERYONE
        """
        staff_IDs = self.staff.dataframe[ self.staff.dataframe['is_secondary'] ]['powerschoolID'].values.tolist()
        queried_cohorts = self.queried_cohorts

        # DEFINE declared_enrollments

        # BECAUSE COHORTS HAVE TO BE CREATED IN DRAGONNET,
        # CHECK FOR THAT SITUATION WHERE WE HAVE COHORTS DECLARED BUT DON'T ACTUALLY
        # EXIST IN THE SYSTEM YET
        # TODO: Present some sort of warning, or something
        declared_names = ['supportstaffALL', 'teachersALL', 'teachersSEC', 'teachersELEM']
        queried_names = queried_cohorts.dataframe.columns.tolist()
        for missing_enrollment in set(declared_names) - set(queried_names):
            queried_cohorts.assign_column(missing_enrollment, to=False)

        # PROGRAMATICALLY SET UP declared_names
        declared_cohorts = PandasDataFrame({'powerschoolID':self.staff.dataframe['powerschoolID'].tolist()})

        self.staff.change_index('powerschoolID')  # THIS REALLY IS NEEDED FOR BELOW STATEMENTS TO WORK
        declared_cohorts.change_index('powerschoolID')
        declared_cohorts.assign_column('supportstaffALL',         to=self.staff.filter('account_type', equals='Support Staff'))
        declared_cohorts.assign_column('teachersSEC',             to=self.staff.filter('account_type', equals='Secondary Teacher'))
        declared_cohorts.assign_column('teachersELEM',            to=self.staff.filter('account_type', equals='Elementary Teacher'))
        declared_cohorts.assign_column('teachersALL',             to=(declared_cohorts.dataframe['teachersSEC'] | declared_cohorts.dataframe['teachersELEM']))

        # FILTER OUT BOTH QUERIED AND DECLARED FOR SECONDARY ONLY
        temp = queried_cohorts.dataframe.reset_index()
        temp = temp[ temp['powerschoolID'].isin(staff_IDs) ]
        staff_queried_cohorts = PandasDataFrame.from_dataframe(temp)
        temp = declared_cohorts.dataframe.reset_index()
        temp = temp[ temp['powerschoolID'].isin(staff_IDs) ]
        staff_declared_cohorts = PandasDataFrame.from_dataframe(temp)

        staff_queried_cohorts.change_index('powerschoolID')
        staff_declared_cohorts.change_index('powerschoolID')

        identify_differences(staff_declared_cohorts,
                             staff_queried_cohorts.set_columns(*declared_names),
                             self.add_user_to_cohort, self.remove_user_from_cohort,
                             None, None)

    def sync_automagic_emails(self):
        """
        """
        # Go through each student, teacher, and schedule information, making a massive defaultdict along the way
        students.change_index('powerschoolID')
        secondary = PandasDataFrame.from_dataframe(students.dataframe[students.dataframe['is_secondary']])
        parents.change_index('studentID')
        email_lists = defaultdict(list)
        ID_to_username = lambda x: secondary.row_column(x, 'orig_username')
        for index, row in secondary.dataframe.iterrows():
            email_lists['students{}'.format(row['grade'])].append(ID_to_username(index))
            email_lists['parents{}'.format(row['grade'])].extend(
                parents.row_column(index, 'emails').split(',')
                )

    def sync_courses(self):
        """
        Makes sure everything in DragonNet matches everything in PowerSchool
        """
        from psmdlsyncer.utils.Utilities import convert_short_long
        
        declared_courses = schedule.dataframe['course'].values
        query = self.get_dn_connection.sql("select id, shortname, fullname from ssismdl_course")()
        queried_courses = PandasDataFrame(query, columns=["id", "shortname", "fullname"])
        queried_courses.change_index('shortname')
        problems = {}
        for _, shortname in schedule.dataframe['course'].iteritems():
            dn_short, dn_long = convert_short_long(shortname, "")
            try:
                get_id = queried_courses.row_column(dn_short, "id")
            except KeyError:
                get_id = None
                if not shortname in problems.keys():
                    problems[shortname] = dn_short

            if not get_id is None:
                self.get_dn_connection.update_table('ssismdl_course', idnumber=shortname, where={'id':get_id})
                self.get_dn_connection.update_table('ssismdl_course', shortname=shortname, where={'id':get_id})
                self.get_dn_connection.update_table('ssismdl_course', summary='', where={'id':get_id})
    
    def sync_sec_parents_cohorts(self):
        """
        sdflksd
        """
        parent_IDs = parents.dataframe['powerschoolID'].values.tolist()
        # DEFINE queried_cohorts
        # QUERY DRAGONNET USING get_user_cohort_enrollments FOR EXISTING ENROLLMENTS
        # SO USE pivot_table TO FORMAT QUERTY RESULT (userid, cohort) INTO A TRUTH-TABLE
        queried_cohorts = self.queried_cohorts

        # DEFINE declared_names

        # BECAUSE COHORTS HAVE TO BE CREATED IN DRAGONNET,
        # CHECK FOR THAT SITUATION WHERE WE HAVE COHORTS DECLARED BUT DON'T ACTUALLY
        # EXIST IN THE SYSTEM YET
        # TODO: Present some sort of warning, or something
        declared_names = ['parentsALL']
        queried_names = queried_cohorts.dataframe.columns.tolist()
        for missing_enrollment in set(declared_names) - set(queried_names):
            queried_cohorts.assign_column(missing_enrollment, to=False)

        # FIXME: SOME PARENTS ARE ALSO TEACHERS... UGH

        # PROGRAMATICALLY SET UP declared_cohorts
        declared_cohorts = PandasDataFrame({'powerschoolID':parent_IDs})
        parents.change_index('powerschoolID')  # THIS REALLY IS NEEDED FOR BELOW STATEMENTS TO WORK
        declared_cohorts.assign_column('parentsALL', to=True)
        declared_cohorts.change_index('powerschoolID')

        identify_differences(declared_cohorts,
                             queried_cohorts.set_columns(*declared_names),
                             self.add_user_to_cohort, self.remove_user_from_cohort,
                             None, None)

    def sync_student_profile_fields(self):
        queried_profile_field_data = self.queried_profile_field_data
        # GET TO SUBSET THAT EXISTS WITHIN DECLARED
        target_columns = self.students.columns_start_with('is')
        queried_columns = queried_profile_field_data.dataframe.columns
        for column in set(target_columns) - set(queried_columns):
            queried_profile_field_data.assign_column(column, to=False)
        queried_filtered = queried_profile_field_data.columns(target_columns)
        embed()
        declared_profile_field_data = self.students.columns(target_columns)

        identify_differences(declared_profile_field_data,
                             queried_filtered,
                             self.add_profile_for_user, self.remove_profile_for_user,
                             None, None)
        embed()

    def sync_sec_students_cohorts(self):
        """
        PARSES students AND QUERIES DRAGONNET, UPDATING DRAGONNET TO MATCH declared_cohorts
        """
        secondary_student_IDs = self.students.dataframe[ self.students.dataframe['is_secondary'] ]['powerschoolID'].values.tolist()
        # DEFINE queried_cohorts
        # QUERY DRAGONNET USING get_user_cohort_enrollments FOR EXISTING ENROLLMENTS
        # SO USE pivot_table TO FORMAT QUERTY RESULT (userid, cohort) INTO A TRUTH-TABLE
        queried_cohorts = self.queried_cohorts

        # DEFINE declared_names

        # BECAUSE COHORTS HAVE TO BE CREATED IN DRAGONNET,
        # CHECK FOR THAT SITUATION WHERE WE HAVE COHORTS DECLARED BUT DON'T ACTUALLY
        # EXIST IN THE SYSTEM YET
        # TODO: Present some sort of warning, or something
        declared_names = ['studentsALL', 'studentsSEC', 'studentsMS', 'studentsHS']
        queried_names = queried_cohorts.dataframe.columns.tolist()
        for missing_enrollment in set(declared_names) - set(queried_names):
            queried_cohorts.assign_column(missing_enrollment, to=False)

        # PROGRAMATICALLY SET UP declared_cohorts
        # MUST BE DECLARED IN SAME ORDER AS ABOVE
        # FIXME: IT SHOULDN'T BE THAT ANNOYING!
        declared_cohorts = PandasDataFrame({'powerschoolID':secondary_student_IDs})
        self.students.change_index('powerschoolID')  # THIS REALLY IS NEEDED FOR BELOW STATEMENTS TO WORK
        declared_cohorts.assign_column('studentsALL', to=True)
        #declared_cohorts.assign_column('testTEST', to=True)
        declared_cohorts.change_index('powerschoolID')  # otherwise, students.filter will get wrong results
        declared_cohorts.assign_column('studentsSEC', to=self.students.filter(column='grade', by_list=range(6, 14)))  #FIXME: CHANGE BACK TO 13
        declared_cohorts.assign_column('studentsMS',  to=self.students.filter(column='grade', by_list=range(6, 9)))
        declared_cohorts.assign_column('studentsHS',  to=self.students.filter(column='grade', by_list=range(9, 14)))  #FIXME: CHANGE BACK TO 13

        # FILTER OUT BOTH QUERIED AND DECLARED FOR SECONDARY ONLY
        temp = queried_cohorts.dataframe.reset_index()
        temp = temp[ temp['powerschoolID'].isin(secondary_student_IDs) ]
        secondary_queried_cohorts = PandasDataFrame.from_dataframe(temp)
        temp = declared_cohorts.dataframe.reset_index()
        temp = temp[ temp['powerschoolID'].isin(secondary_student_IDs) ]
        secondary_declared_cohorts = PandasDataFrame.from_dataframe(temp)

        secondary_queried_cohorts.change_index('powerschoolID')
        secondary_declared_cohorts.change_index('powerschoolID')

        identify_differences(secondary_declared_cohorts,
                                  secondary_queried_cohorts.set_columns(*declared_names),
                                  self.add_user_to_cohort, self.remove_user_from_cohort,
                                  None, None)
        
if __name__ == "__main__":

    requires_setting('DIRECTORIES', 'path_to_powerschool_dump')
    full_path = lambda _file: config['DIRECTORIES'].get('path_to_powerschool_dump') + '/' + _file

    # TODO: MAKE SURE THEY GET THE LATEST VERSION AUTOMAGICALLY?
    # TODO: FIGURE OUT A WAY TO GET THE HEADERS IN POWERSCHOOL FILE
    students = PandasDataFrame.from_csv(full_path('ssis_dist_studentinfo_v3.0'),
                                        header=None,
                                        names=["powerschoolID", "id",
                                               "grade", "homeroom", "fullname", "emails", "entrydate", "nationality", "delete"],
                                        dtype={'powerschoolID':np.object},
                                        index_col=False,
                                        converters={6:pd.to_datetime})
    staff = PandasDataFrame.from_csv(full_path('ssis_dist_staffinfo_v3.0'),
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
    courses = PandasDataFrame.from_csv(full_path('ssis_sec_courseinfo_v3.0'),
                                       header=None,
                                       names=["course", "name", "delete"],
                                       index_col=False)
    allocations = PandasDataFrame.from_csv(full_path('ssis_sec_teacherallocations_v3.0'),
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
    staff.assign_column('account_type',     from_column={
        'staff_status': lambda ss: {0:'Elementary Teacher', 1:'Secondary Teacher', 2:'Support Staff'}.get(ss, 'Undefined')
        })
    staff.assign_column('is_secondary',     to=staff.dataframe['staff_status']==1)
    staff.assign_column('is_elementary',    to=staff.dataframe['staff_status']==0)

    # IT'S STUFF LIKE THIS THAT DRIVES ME CRAZY
    staff.assign_column('powerschoolID',   from_column={'powerschoolID': lambda x: x if re.match('^[0-9]+$', str(x)) else re.sub('[^0-9]', '', str(x))})

    # set up schedule
    

    # set up students
    students.assign_column('emails',        from_column={'emails': lambda x: x.lower()})  # how bad is this?
    students.assign_column('section',       from_column={'grade':determine_section})
    students.assign_column('first',         to=students.split_column_text('fullname', NAMESPLIT, 1))
    students.assign_column('last',          to=students.split_column_text('fullname', NAMESPLIT, 0))
    students.assign_column('name',          by_iterrows=lambda index, row: row['first'] + ' ' + row['last'])
    students.assign_column('graduation',    from_column={'grade':get_year_of_graduation})
    students.assign_column('orig_username', by_iterrows=derive_username)
    students.assign_column('yearsenrolled', from_column={'entrydate':get_years_since_enrolled})
    students.assign_column('parentID',      from_column={'powerschoolID':lambda x: str(x)[:4]+'P'})

    students.assign_column('issecstudent',  from_column={'grade':lambda x: int(x) in range(6, 13)})
    students.assign_column('iselemstudent', from_column={'grade':lambda x: int(x) in range(1, 6)})
    students.assign_column('ishsstudent',  from_column={'grade':lambda x: int(x) in range(9, 13)})
    students.assign_column('ismsstudent',from_column={'grade':lambda x: int(x) in range(6, 10)})
    #students.assign_column('is_german',      from_column={'nationality': lambda x: True if x == 'Germany' else False})
    #students.assign_column('is_chinese',      from_column={'nationality': lambda x: True if x in ['China', 'Taiwan', 'Malaysia'] else False})
    # STR IS USED FOR PRINTING OUT INFORMATION ABOUT THE STUDENT
    students.assign_column('str',           by_iterrows=lambda index, row: "[ {0: <22} ({1}) ]".format(row['orig_username'], row['powerschoolID']))

    # SET UP PARENTS, WHICH IS A SPECIAL CASE
    parents = PandasDataFrame({'powerschoolID':students.dataframe['parentID']})
    parents.assign_column('studentID',     to=students.dataframe['powerschoolID'].values)
    parents.assign_column('emails',         to=students.dataframe['emails'].values)
    parents.assign_column('isparent',       to=True)
    

    allocations.assign_column('grade',      from_column={'coursename':determine_grade_from_coursename})

    sync = Sync(students, staff, parents, schedule, allocations)

    #sync.sync_courses()

    if flag_passed('sync_profile_fields'):
        sync.sync_student_profile_fields()

    if flag_passed('enroll_cohorts'):
        sync.sync_staff_cohorts()    #FIXME: POWERSCHOOL IDs HAVE TO WORK FOR EVERYONE THE SAME WAY
        #sync.sync_sec_parents_cohorts()
        #sync.sync_sec_students_cohorts()
    if flag_passed('enroll_groups'):
        sync.sync_sec_students_enrollments()

