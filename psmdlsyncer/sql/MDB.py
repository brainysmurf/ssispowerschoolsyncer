from psmdlsyncer.db import DBSession
from psmdlsyncer.db import MoodleDB    # yes, import the module itself, used for getattr statements
from psmdlsyncer.db.MoodleDB import *  # and, yes, import all the terms we need to refer to the tables as classes
from sqlalchemy import and_, not_, or_
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import desc, asc
from psmdlsyncer.utils import NS2
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.utils import time_now
from sqlalchemy import func, case
from sqlalchemy.orm import aliased

import logging

class MoodleDBSess:
    """
    Implements lower-level convenience methods that handles sessions, transactions, queries
    Errors are not trapped, should be handled at higher level
    """
    def __init__(self):
        ns = NS2()
        self.logger = logging.getLogger('MoodleDBSess')
        self.default_logger = self.logger.info

    def table_string_to_class(self, table):
        """
        This provides the whole class with an API whereby
        table_name can be a string that equals the equiv in the actual database
        so that places outside of me don't have to do a bunch of imports
        TODO: Find the native sqlalchemy way of doing this conversion
        @table should be a string
        @returns Database class that can be used in queries
        """
        if table.lower().endswith('data'):
            table = table[:-4] + 'datum'
        if table.endswith('s'):
            table = table[:-1]
        ret = getattr(MoodleDB, table.replace('_', ' ').title().replace(' ', ''))
        return ret

    def wrap_no_result(self, f, *args, **kwargs):
        """
        For simple work, returns None if NoResultFound is encountered
        Most useful when calling an sqlalchemy function like one() and you want
        a simple way to handle an error
        """
        try:
            return f(*args, **kwargs)
        except NoResultFound:
            return None

    def insert_table(self, table, **kwargs):
        with DBSession() as session:
            table_class = self.table_string_to_class(table)
            instance = table_class()
            for key in kwargs.keys():
                setattr(instance, key, kwargs[key])

            session.add(instance)

    def get_rows_in_table(self, table, **kwargs):
        """
        @table string of the table name (without the prefix)
        @param kwargs is the where statement
        """
        table_class = self.table_string_to_class(table)
        with DBSession() as session:
            statement = session.query(table_class).filter_by(**kwargs)
        return statement.all()

    def update_table(self, table, where={}, **kwargs):
        """
        Can only update one row...
        """
        table_class = self.table_string_to_class(table)
        with DBSession() as session:
            instance = session.query(table_class).filter_by(**where).one()
            for key in kwargs.keys():
                setattr(instance, key, kwargs[key])
            session.add(instance)

    def get_user_from_idnumber(self, idnumber):
        with DBSession() as session:
            try:
                ret = session.query(User).filter(User.idnumber == idnumber).one()
            except MultipleResultsFound:
                self.logger.critical("More than one user with this idnumber: {}".format(idnumber))
                ret = None
            except NoResultFound:
                ret = None
        return ret

    def get_user_from_username(self, username):
        with DBSession() as session:
            ret = session.query(User).filter(User.username == username).one()
        return ret

    def get_column_from_row(self, table, column, **kwargs):
        table_class = self.table_string_to_class(table)
        with DBSession() as session:
            try:
                result = session.query(table_class).filter_by(**kwargs).one()
            except NoResultFound:
                result = None
        if not result:
            return None
        return getattr(result, column)

    def get_list_of_attributes(self, table, attr):
        """
        """
        table_class = self.table_string_to_class(table)
        with DBSession() as session:
            instance = session.query(table_class)
        return [getattr(obj, attr) for obj in instance.all()]

    def parse_user(self, user):
        if isinstance(user, str):
            # passed an idnumber, so let's get the object
            return self.get_user_from_idnumber(user)
        return user

    def get_user_custom_profile_field(self, user, field_name):
        """
        @param user can be an object or just the idnumber
        @return the value of the custom profile object
        """
        user = self.parse_user(user)
        with DBSession() as session:
            statement = session.query(UserInfoDatum).\
                join(UserInfoField, UserInfoField.id == UserInfoDatum.fieldid).\
                    filter(and_(
                        UserInfoField.shortname == field_name,
                        UserInfoDatum.userid == user.id
                        )
                    )
            try:
                ret = statement.one()
            except MultipleResultsFound:
                self.logger.warning("Multiple fields for {0.username} and {1}; using first() ".format(user, field_name))
                ret = statement.first()
        return ret

class MoodleDBSession(MoodleDBSess):
    """
    High-level convenience routines that handles sessions, transactions, queries
    The difference between high-level and low-level may be up to this programmer's imagination :)
    But basically, anything obviously 'dragonnet-y' is here
    """
    SYSTEM_CONTEXT = 1
    MRBS_EDITOR_ROLE = 10
    TEACHING_LEARNING_CATEGORY_ID = config_get_section_attribute('MOODLE', 'tl_cat_id')

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        with DBSession() as session:
            needed_cohorts = ['teachersALL', 'parentsALL', 'studentsALL', 'supportstaffALL']
            for cohort in needed_cohorts:
                exists = session.query(Cohort).filter_by(idnumber=cohort).all()
                if not exists:
                    self.add_cohort(cohort, cohort)

    def users_enrolled_in_this_cohort(self, cohort):
        """
        Returns users in this cohort
        @param cohort should be the cohort idnumber
        """
        and_portion = [Cohort.idnumber == c for c in cohort]
        with DBSession() as session:
            all_users = session.query(User).\
                select_from(CohortMember).\
                    join(Cohort, Cohort.id == CohortMember.cohortid).\
                    join(User, User.id == CohortMember.userid).\
                        filter(
                            Cohort.idnumber == cohort
                        )
            yield from all_users.all()

    def users_enrolled_in_these_cohorts(self, cohort):
        """
        Returns users
        @param cohort must be an iterator
        TODO: Do I need to process for repeats?
        """
        or_portion = [Cohort.idnumber == c for c in cohort]
        with DBSession() as session:
            all_users = session.query(User)\
                .select_from(CohortMember).\
                    join(Cohort, Cohort.id == CohortMember.cohortid).\
                    join(User, User.id == CohortMember.userid).\
                        filter(
                            or_(
                                *or_portion
                            ),
                        )
            yield from all_users.all()

    def add_cohort(self, idnumber, name):
        exists = self.get_rows_in_table('cohort', idnumber=idnumber)
        if exists:
            self.default_logger('Did NOT create cohort {} as it already exists!'.format(idnumber))
            return
        now = time_now()

        with DBSession() as session:
            cohort = Cohort()
            cohort.idnumber = idnumber
            cohort.name = name
            cohort.descriptionformat = 0
            cohort.description = ''
            cohort.contextid = self.SYSTEM_CONTEXT
            cohort.source="psmdlsyncer"
            cohort.timecreated = time_now()
            cohort.timemodified = time_now()
            session.add(cohort)

    def bell_schedule(self):
        """
        Query that represents the schedule, using Moodle's terms
        Sorted using order by Role.name ASC because
        we need the order to be in Teacher, Parent, Student
        because teacher info needed to complete the group
        TODO: Figure out how to get specific ordering from SQL
              and then incorporate Manager status too
        """

        with DBSession() as session:
            schedule = session.query(
                    Course.idnumber.label("courseID"), User.idnumber.label("userID"), User.username.label('username'), Role.shortname.label('rolename'), Group.name.label('groupName')
                    ).select_from(Course).\
                        join(CourseCategory, CourseCategory.id == Course.category).\
                        join(Context, Course.id == Context.instanceid).\
                        join(RoleAssignment, RoleAssignment.contextid == Context.id).\
                        join(User, User.id == RoleAssignment.userid).\
                        join(Role, Role.id == RoleAssignment.roleid).\
                        join(GroupsMember, GroupsMember.userid == User.id).\
                        join(Group, and_(
                            Group.id == GroupsMember.groupid,
                            Group.courseid == Course.id
                            )).\
                        filter(
                            and_(
                                # CourseCategory.path.like('/{}/%'.format(self.TEACHING_LEARNING_CATEGORY_ID)),   # TODO: get roleid on __init__
                                CourseCategory.path.like('/{}/%'.format(self.TEACHING_LEARNING_CATEGORY_ID)),   # TODO: get roleid on __init__
                                Group.name != None,
                                Course.idnumber != '',
                                User.idnumber != '',
                            )).\
                        order_by(asc(Role.id))   # sort by role.id because it's in the natural order expected (teachers first, then students, then parents)
            yield from schedule.all()

    def get_mrbs_editors(self):
        with DBSession() as session:
            statement = session.query(User).\
                select_from(RoleAssignment).\
                    join(User, RoleAssignment.userid == User.id).\
                        filter(
                            and_(
                                RoleAssignment.contextid == self.SYSTEM_CONTEXT,
                                RoleAssignment.roleid == self.MRBS_EDITOR_ROLE,
                                not_(User.idnumber.like(''))
                            )
                        )
        yield from statement.all()

    def add_mrbs_editor(self, user_idnumber):
        user = self.wrap_no_result(self.get_user_from_idnumber, user_idnumber)
        if not user:
            # no such user, don't do it!
            return

        now = time_now()
        self.insert_table(
            'role_assignments',
            contextid=self.SYSTEM_CONTEXT,
            roleid=self.MRBS_EDITOR_ROLE,
            userid=user.id,
            modifierid=2, # TODO: Admin ID, right?
            component='psmdlsyncer',  # Might as well use it for something?
            itemid=0,
            sortorder=0,
            timemodified=now)

    def get_user_schoolid(self, user):
        obj = self.get_user_custom_profile_field(user, 'schoolid')
        if not obj:
            return None
        return obj.data

    def get_teaching_learning_courses(self):
        """ Returns a set of id of courses that are in teaching/learning """
        with DBSession() as session:
            statement = session.query(Course.idnumber, Course.fullname, CourseSsisMetadatum.value.label('grade'), Course.id.label('database_id')).\
                join(CourseCategory, CourseCategory.id == Course.category).\
                outerjoin(CourseSsisMetadatum,
                    and_(
                        CourseSsisMetadatum.courseid == Course.id,
                        CourseSsisMetadatum.field.like('grade%')
                        )).\
                filter(and_(
                    not_(Course.idnumber == ''),
                    CourseCategory.path.like('/{}/%'.format(self.TEACHING_LEARNING_CATEGORY_ID))
                    )).\
                order_by(Course.fullname,   CourseSsisMetadatum.value)
        yield from statement.all()

    def get_teaching_learning_courses2(self):
        """ Returns a set of id of courses that are in teaching/learning """

        with DBSession() as session:
            sub = session.query(Course.id.label('course_id'), func.count('*').label('grade_count')).\
                select_from(Course).\
                    join(CourseSsisMetadatum,
                        and_(
                            CourseSsisMetadatum.courseid == Course.id,
                            CourseSsisMetadatum.field.like('grade%')
                        )
                    ).\
                    group_by(Course.id).subquery()

            statement = session.query(Course, sub.c.grade_count).\
                outerjoin(sub, Course.id == sub.c.course_id).\
                    order_by(Course.id)
        yield from statement.all()

    def get_custom_profile_records(self):
        with DBSession() as session:
            statement = session.\
                query(User.idnumber, User.username, UserInfoField.shortname, UserInfoDatum.data).\
                    select_from(UserInfoDatum).\
                join(UserInfoField, UserInfoField.id == UserInfoDatum.fieldid).\
                join(User, User.id == UserInfoDatum.userid)
        yield from statement.all()

    def get_custom_profile_fields(self):
        """
        Returns just the data in user_info_fields
        """
        with DBSession() as session:
            statement = session.\
                query(UserInfoField)
        yield from statement.all()

    def get_parent_student_links(self):
        with DBSession() as session:
            Child = aliased(User)
            statement = session.\
                query(User.idnumber, Child.idnumber).\
                select_from(User).\
                join(RoleAssignment, RoleAssignment.userid == User.id).\
                join(Role, Role.id == RoleAssignment.roleid).\
                join(Context,
                    and_(
                        Context.id == RoleAssignment.contextid,
                        Context.contextlevel == 30
                    )).\
                join(Child, Child.id == Context.instanceid).\
                filter(Role.shortname == 'parent').\
                order_by(User.idnumber)
        yield from statement.all()


    def set_user_custom_profile(self, user_idnumber, name, value):
        user = self.get_user_from_idnumber(user_idnumber)
        if not user:
            self.logger.warning("Custom profile field for a user was requested, but no such user:".format(user_idnumber))
            return  # some error, right?
        userid = user.id

        fieldid = self.get_column_from_row('user_info_field', 'id', shortname=name)

        if not fieldid:
            return

        self.update_table('user_info_data', where=dict(
            userid=userid,
            fieldid=fieldid
            ),
            data=value
            )

    def make_new_custom_profile_field(self, name):
        """
        Do database stuff to create the custom user profile field
        """
        with DBSession() as session:
            exists = session.query(UserInfoField).filter(UserInfoField.name == name).all()
        if exists:
            print('Already there buddy')
            return


        with DBSession() as session:
            result = session.query(UserInfoField.sortorder).order_by(desc(UserInfoField.sortorder)).limit(1).first()
        if not result:
            lastsort = 0
        else:
            lastsort = int(result.sortorder)

        sort = lastsort + 1
        ns = NS2()
        ns.shortname = name
        ns.name = name.replace("_", " ").title()
        ns.description = ""
        ns.descriptionformat = 1
        ns.categoryid = 1
        ns.sortorder = sort
        ns.required = 0
        ns.locked = 1
        ns.visible = 0
        ns.forceunique = 0
        ns.signup = 0
        ns.defaultdata = 0
        ns.defaultdataformat = 0
        ns.param1 = "psmdlsyncer"  # for debugging...
        ns.param2 = ""
        ns.param3 = ""
        ns.param4 = ""
        ns.param5 = ""

        if name.startswith('is'):
            ns.datatype = "checkbox"
        else:
            # for everything...?
            ns.datatype = "text"
        self.insert_table('user_info_field', **ns.kwargs)

    def add_user_custom_profile(self, user_idnumber, name, value):
        """
        """
        user = self.wrap_no_result(self.get_user_from_idnumber, user_idnumber)
        if not user:
            return
        user_id = user.id  # needed later

        with DBSession() as session:
            try:
                field = session.query(UserInfoField).filter_by(shortname=name).one()  # shortname == idnumber
            except NoResultFound:
                self.logger.info("User has a custom profile field {} but it doesn't exist yet".format(name))
                return
            except MultipleResultsFound:
                self.logger.info("Multiple, using first (again)")
                field = session.query(UserInfoField).filter_by(shortname=name).first()

            exists = session.query(UserInfoDatum).filter_by(fieldid=field.id, userid=user_id).all()
            if exists:
                self.default_logger("Not creating entry for field {} for user {} because it already exists!".format(name, user_idnumber))
                return
            # check for multiples?
            user_info = UserInfoDatum()
            user_info.userid = user_id
            user_info.fieldid = field.id
            if field.datatype == 'checkbox':
                user_info.data = int(value)
            else:
                user_info.data = value
            user_info.dateformat = 0
            session.add(user_info)

    def get_cohorts(self):
        with DBSession() as session:
            statement = session.query(User.idnumber, Cohort.idnumber).\
                select_from(CohortMember).\
                    join(Cohort, Cohort.id == CohortMember.cohortid).\
                    join(User, User.id == CohortMember.userid)

        yield from statement.all()

if __name__ == "__main__":

    m = MoodleDBSession()

    # for item in m.get_custom_profile_records():
    #     print(item)

    # result = m.wrap_no_result(m.get_user_from_idnumber, 'xxxx')
    # assert(result is None)

    # for item in m.users_enrolled_in_these_cohorts(['supportALL']):
    #     print(item.idnumber)

    # assert( m.parse_user('38110') in list(m.mrbs_editors()) )
    # assert(m.get_user_schoolid('38110') == '112')

    for user in m.mrbs_editors():
        from IPython import embed
        embed()
        print(user)

    # for student, parent in m.get_parent_student_links():
    #     print(student)
    #     print(parent)
    #     print()

    # for item, number in m.get_teaching_learning_courses2():
    #     print(item.fullname)
    #     print(number)
    #     # print("{} {}".format(course.fullname, course.grade))

    # for item in m.get_teaching_learning_courses():
    #     input()
    #     print(item)

    # m.add_cohort('blahblahALL', 'All Parents')


