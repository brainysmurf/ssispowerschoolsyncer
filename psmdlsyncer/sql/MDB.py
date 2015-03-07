from psmdlsyncer.db import DBSession
from psmdlsyncer.db import MoodleDB    # yes, import the module itself, used for getattr statements
from psmdlsyncer.db.MoodleDB import *  # and, yes, import all the terms we need to refer to the tables as classes
from sqlalchemy import and_, not_, or_
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import desc, asc
from psmdlsyncer.utils import NS2
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.utils import time_now
from sqlalchemy import func, case, Integer, String
from sqlalchemy.dialects.postgres import ARRAY
from sqlalchemy.orm import aliased
from collections import defaultdict
from sqlalchemy.sql.expression import cast

import logging
import re

class MoodleDBSess:
    """
    Implements lower-level convenience methods that handles sessions, transactions, queries
    Errors are not trapped, should be handled at higher level
    """
    def __init__(self):
        ns = NS2()
        self.logger = logging.getLogger('MoodleDBSess')
        self.default_logger = self.logger.info
        self.DBSession = DBSession
        self.and_ = and_

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

    def delete_table(self, table, **kwargs):
        with DBSession() as session:
            table_class = self.table_string_to_class(table)
            table_class.delete(**kwargs)

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

    def get_course_from_idnumber(self, idnumber):
        with DBSession() as session:
            try:
                ret = session.query(Course).filter(Course.shortname == idnumber).one()
            except MultipleResultsFound:
                self.logger.critical("More than one course with this idnumber: {}".format(idnumber))
                ret = None
            except NoResultFound:
                ret = None
        return ret

    def get_user_from_username(self, username):
        with DBSession() as session:
            ret = session.query(User).filter(User.username == username).one()
        return ret

    def set_user_idnumber_from_username(self, username, idnumber):
        with DBSession() as session:
            ret = session.query(User).filter(User.username == username).one()
            ret.idnumber = idnumber

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

    def get_online_portfolios(self):
        with DBSession() as session:
            statement = session.query(Course).filter(Course.idnumber.startswith('OLP:'))

        for row in statement.all():
            yield re.sub(r'^OLP:', '', row.idnumber)


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
                            and_(Cohort.idnumber == cohort, User.deleted == 0)
                        )
            for item in all_users.all():
                yield item

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
            for item in all_users.all():
                yield item

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
                                #CourseCategory.path == ('/{}'.format(self.TEACHING_LEARNING_CATEGORY_ID)),   # TODO: get roleid on __init__
                                CourseCategory.path.like('/{}/%'.format(self.TEACHING_LEARNING_CATEGORY_ID)),   # TODO: get roleid on __init__
                                Group.name != None,
                                Course.idnumber != '',
                                User.idnumber != '',
                            )).\
                        order_by(asc(Role.id))   # sort by role.id because it's in the natural order expected (teachers first, then students, then parents)
            for item in schedule.all():
                yield item

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
        for item in statement.all():
            yield item

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

    def get_timetable_table(self):
        with DBSession() as session:
            statement = session.query(SsisTimetableInfo, User.idnumber).\
                join(User, User.id == SsisTimetableInfo.studentuserid)
        for item in statement.all():
            yield item

    def get_course_metadata(self):
        with DBSession() as session:
            statement = session.query(
                Course.idnumber.label('course_idnumber'),
                CourseSsisMetadatum.value.label('course_grade')).\
            select_from(CourseSsisMetadatum).\
            join(Course, Course.id == CourseSsisMetadatum.courseid).\
            filter(CourseSsisMetadatum.field.like('grade%')).\
            order_by(Course.idnumber, CourseSsisMetadatum.value)

        for item in statement.all():
            yield item

    def add_course_metadata(self, course_metadata):
        with DBSession() as session:
            try:
                course = session.query(Course).filter_by(idnumber=course_metadata.course_idnumber).one()
            except NoResultFound:
                self.default_logger("No course by idnumber when adding metadata {}".format(course_metadata.course_idnumber))
                return
            except MultipleResultsFound:
                self.logger.warning("Multiple courses with idnumber {}".format(course_metadata.course_idnumber))
                return

            for i in range(len(course_metadata.course_grade)):
                grade = course_metadata.course_grade[i]
                grade_str = "grade{}".format(i+1)
                new = CourseSsisMetadatum()
                new.courseid = course.id
                setattr(new, 'field', grade_str)
                setattr(new, 'value', grade)

                exists = session.query(CourseSsisMetadatum).filter_by(
                    courseid=course.id,
                    field=grade_str,
                    value=grade
                    ).all()
                if exists:
                    self.logger.default_logger('Course Metadata already exists')
                    continue
                session.add(new)

    def get_teaching_learning_courses(self):
        """
        Returns course information for any course that is within the Teaching & Learning menu
        Including the grade info stored in course_ssis_metadata
        Grade info is a string, if there are more than two then is in 11,12 format
        TODO: Sometimes it formats as 12/11, make it sort (but if you sort you have to put in group_by)
              Workaround: the model just sorts it for us
        """

        with DBSession() as session:
            sub = session.query(
                Course.id.label('course_id'),
                func.string_agg(CourseSsisMetadatum.value, ',').label('grade')).\
                select_from(Course).\
                    join(CourseCategory, CourseCategory.id == Course.category).\
                    join(CourseSsisMetadatum,
                        and_(
                            CourseSsisMetadatum.courseid == Course.id,
                            CourseSsisMetadatum.field.like('grade%')
                        )
                    ).\
                    filter(and_(
                        not_(Course.idnumber == ''),
                        #CourseCategory.path == '/{}'.format(self.TEACHING_LEARNING_CATEGORY_ID)
                        CourseCategory.path.like('/{}/%'.format(self.TEACHING_LEARNING_CATEGORY_ID))
                        )).\
                    group_by(Course.id).\
                    subquery()

            statement = session.query(Course.idnumber, Course.fullname, sub.c.grade, Course.id.label('database_id')).\
                join(sub, Course.id == sub.c.course_id).\
                    order_by(Course.id)

        for item in statement.all():
            yield item

    def get_custom_profile_records(self):
        with DBSession() as session:
            statement = session.\
                query(User.idnumber, User.username, UserInfoField.shortname, UserInfoDatum.data).\
                    select_from(UserInfoDatum).\
                join(UserInfoField, UserInfoField.id == UserInfoDatum.fieldid).\
                join(User, User.id == UserInfoDatum.userid)
        for item in statement.all():
            yield item

    def get_custom_profile_fields(self):
        """
        Returns just the data in user_info_fields
        """
        with DBSession() as session:
            statement = session.\
                query(UserInfoField)
        for item in statement.all():
            yield item

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
        for item in statement.all():
            yield item

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
                return

            result = session.query(UserInfoField.sortorder).order_by(desc(UserInfoField.sortorder)).limit(1).first()
            if not result:
                lastsort = 0
            else:
                lastsort = int(result.sortorder)

            sort = lastsort + 1
            user_info_field = UserInfoField()
            user_info_field.shortname = name
            user_info_field.name = name.replace("_", " ").title()
            user_info_field.description = ""
            user_info_field.descriptionformat = 1
            user_info_field.categoryid = 1
            user_info_field.sortorder = sort
            user_info_field.required = 0
            user_info_field.locked = 1
            user_info_field.visible = 0
            user_info_field.forceunique = 0
            user_info_field.signup = 0
            user_info_field.defaultdata = 0
            user_info_field.defaultdataformat = 0
            user_info_field.param1 = "psmdlsyncer"  # for debugging...
            user_info_field.param2 = ""
            user_info_field.param3 = ""
            user_info_field.param4 = ""
            user_info_field.param5 = ""

            if name.startswith('is'):
                user_info_field.datatype = "checkbox"
            else:
                # for everything...?
                user_info_field.datatype = "text"

            session.add(user_info_field)

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

        for item in statement.all():
            yield item

    def clear_active_timetable_data(self):
        with DBSession() as session:
            statement = session.query(SsisTimetableInfo)
            for row in statement.all():
                row.active = 0

    def get_timetable_data(self, active_only=True):
        with DBSession() as session:
            Teacher = aliased(User)
            Student = aliased(User)
            statement = session.query(
                SsisTimetableInfo.id,
                Course.idnumber.label('course_idnumber'),
                Teacher.idnumber.label('teacher_idnumber'),
                Student.idnumber.label('student_idnumber'),
                SsisTimetableInfo.name,
                SsisTimetableInfo.period,
                SsisTimetableInfo.comment,
                SsisTimetableInfo.active
                ).\
            select_from(SsisTimetableInfo).\
                join(Course, Course.id == SsisTimetableInfo.courseid).\
                join(Teacher, Teacher.id == SsisTimetableInfo.teacheruserid).\
                join(Student, Student.id == SsisTimetableInfo.studentuserid)
            if active_only:
                statement = statement.filter(SsisTimetableInfo.active == 1)
        return statement.all()

    def set_timetable_data_inactive(self, timetable):
        with DBSession() as session:
            ns = NS2()
            try:
                ns.courseid = session.query(Course).filter_by(shortname=timetable.course.idnumber).one().id
                ns.studentuserid = session.query(User).filter_by(idnumber=timetable.student.idnumber).one().id
                ns.teacheruserid = session.query(User).filter_by(idnumber=timetable.teacher.idnumber).one().id
            except NoResultFound:
                self.logger.warning('No results found for timetable object when setting to inactive {}'.format(timetable))
            except MultipleResultsFound:
                self.logger.warning('Multiple results found for timetable object {}'.format(timetable))
                return
            ns.name = timetable.group.idnumber
            exist = session.query(SsisTimetableInfo).\
                filter_by(
                    **ns.kwargs
                    ).all()

            for row in exist:
                row.active = 0


    def add_timetable_data(self, timetable):
        with DBSession() as session:
            ns = NS2()
            ns.courseid, ns.studentuserid, ns.teacheruserid = (None, None, None)
            try:
                ns.courseid = session.query(Course).filter_by(shortname=timetable.course.idnumber).one().id
                ns.studentuserid = session.query(User).filter_by(idnumber=timetable.student.idnumber).one().id
                ns.teacheruserid = session.query(User).filter_by(idnumber=timetable.teacher.idnumber).one().id
            except NoResultFound:
                if ns.courseid:
                    self.logger.debug('No results found for timetable object when adding {}'.format(timetable))
                return
            except MultipleResultsFound:
                self.logger.warning('Multiple results found for timetable object {}'.format(timetable))
                return
            ns.name = timetable.group.idnumber
            ns.period = timetable.period_info
            ns.grade = timetable.course.convert_grade()

            exist = False
            try:
                exist = session.query(SsisTimetableInfo).filter_by(**ns.kwargs).one()
            except NoResultFound:
                pass

            if exist:                
                if not exist.active:
                    self.logger.warning('Timetable {} was inactive, setting to active'.format(timetable))
                    exist.active = 1
                else:
                    self.logger.warning("Timetable {} already exists!".format(timetable))

            else:
                new = SsisTimetableInfo()
                for key in ns.kwargs:
                    setattr(new, key, getattr(ns, key))
                new.comment = timetable.group.section
                new.active = 1

                session.add(new)

    def set_timetable_data_active(self, timetable):
        # TODO: Figure this out so that I'm not repeating code...
        with DBSession() as session:
            ns = NS2()
            try:
                ns.courseid = session.query(Course).filter_by(shortname=timetable.course).one().id
                ns.studentuserid = session.query(User).filter_by(idnumber=timetable.student).one().id
                ns.teacheruserid = session.query(User).filter_by(idnumber=timetable.teacher).one().id
            except NoResultFound:
                self.logger.warning('No results found for timetable object when setting to active {}'.format(timetable))
                return
            except MultipleResultsFound:
                self.logger.warning('Multiple results found for timetable object {}'.format(timetable))
                return
            ns.name = timetable.group.idnumber
            ns.period = timetable.period_info

            this = session.query(SsisTimetableInfo).\
                filter_by(
                    **ns.kwargs
                    ).one()
            this.active = 1

    def undelete_user(self, user):
        with DBSession() as session:
            this_user = session.query(User).filter_by(idnumber=user.idnumber).one()
            this_user.deleted = 0

if __name__ == "__main__":

    m = MoodleDBSession()

    # for item in m.get_custom_profile_records():
    #     print(item)

    # result = m.wrap_no_result(m.get_user_from_idnumber, 'xxxx')
    # assert(result is None)

    for item in m.users_enrolled_in_these_cohorts(['studentsALL']):
        print(item.idnumber)

    # assert( m.parse_user('38110') in list(m.mrbs_editors()) )
    # assert(m.get_user_schoolid('38110') == '112')

    # for user in m.mrbs_editors():
    #     print(user)

    # for student, parent in m.get_parent_student_links():
    #     print(student)
    #     print(parent)
    #     print()

    # for item in m.get_timetable_data():
    #     input(item)


    # for item in m.get_course_metadata():
    #     print(item)
    #     input()


    # m.add_cohort('blahblahALL', 'All Parents')


    # for item in m.get_online_portfolios():
    #     print(item)

