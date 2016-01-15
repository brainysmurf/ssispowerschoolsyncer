from psmdlsyncer.models.datastores.tree import AbstractTree
from psmdlsyncer.files import AutoSendImport
from psmdlsyncer.models.datastores.branch import DataStore
from psmdlsyncer.settings import config, config_get_section_attribute
from psmdlsyncer.utils import NS2
from psmdlsyncer.files import clear_folder
from collections import defaultdict
from psmdlsyncer.db import DBSession
from psmdlsyncer.db.MoodleDB import *
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound
import re, os, sys, pwd
from sqlalchemy import and_, not_, or_
import subprocess

import pickle
import gns

def put_in_order(what, reverse=False):
    what = what.upper()
    result = 1 # elementary don't have LEARN
    if reverse:
        trans = {'L':8,'E':7,'A':6,'R':5,'N':4,'S':3,'SWA':2,'JS':1}
    else:
        trans = {'L':1,'E':2,'A':3,'R':4,'N':5,'S':6,'SWA':7, 'JS':8}
    if '6' in what:
        result = 100 + trans[re.sub('[0-9]', '', what)]
    elif '7' in what:
        result =  200 + trans[re.sub('[0-9]', '', what)]
    elif '8' in what:
        result =  300 + trans[re.sub('[0-9]', '', what)]
    elif '9' in what:
        result =  400 + trans[re.sub('[0-9]', '', what)]
    elif '10' in what:
        result = 500 + trans[re.sub('[0-9]', '', what)]
    elif '11' in what:
        result = 600 + trans[re.sub('[0-9]', '', what)]
    elif '12' in what:
        result = 700 + trans[re.sub('[0-9]', '', what)]
    elif re.sub('[1..9]', '', what):
        result = ord(re.sub('[1..9]', '', what)[0])
    return result

def excluded_from_chinese_list(student):
    """
    Return true if parents explicitely ask us to exclude them
    This happens with some students, like Singapore
    There should be a field in PowerSchool, that lists what language they speak
    Of course it should, it isn't because... well, let's not go there.
    """
    if student.family_id in ['3094P']:
        return True
    return False

def name_to_email(long_name):
    """
    USED FOR ACTIVITIES EMAIL GENERATION
    TODO: MOVE TO utils
    """
    try:
        where = long_name.index(')')
    except ValueError:
        return None
    where += 1
    long_name = long_name[where:].strip().lower()
    return re.sub('[^a-z0-9]', '', long_name)

from psmdlsyncer.utils.BulkManager import BulkEmailManager

class AutoSendTree(AbstractTree):
    pickup = DataStore
    klass = AutoSendImport
    convert_course = True

    home = gns.config.directories.home

    def process(self):
        """
        Overrides default behavior in order to do some pre-flight stuff
        """ 
        self._processed = True
        # We need to load up previous section_maps info
        with open(os.path.join(self.home, 'section_maps'), 'rb') as _file:
            section_maps = pickle.load(_file)

        # This will ensure that sections persist with the same -a, -b nomenclature over time
        self.groups.section_maps = section_maps
        self.groups.period_info = {}

        super().process()

    def process_mrbs_editor(self):
        for teacher in self.teachers.get_objects():
            self.mrbs_editor.make(teacher.ID)

    def output_parent_bulk_emails(self):
        self.build_automagic_emails()
        import click
        the_list = list(self.usebccparentsHOMEROOM.keys())
        the_list.sort(key=put_in_order)

        for homeroom in the_list:
            click.echo('<a href="mailto:?bcc=usebccparents{0}@student.ssis-suzhou.net">usebccparents{0}@student.ssis-suzhou.net</a><br />'.format(homeroom))

    def run_newaliases(self):
        """
        Runs newaliases
        """
        newaliases_path = gns.config.email.newaliases_path
        if newaliases_path:
            self.logger.info("Running newaliases")
            p = subprocess.Popen(newaliases_path, shell=True)
            self.logger.info(p.communicate())
        else:
            self.logger.warn("newaliases not run!")

    def output_json(self):
        self.bm.output_json()

    def output_all_aliases(self):
        self.bm.output_all_aliases()

    def build_automagic_emails(self, make_new_students=False):

        self.bm = BulkEmailManager()

        self.logger.debug("Setting email lists")

        # Set up the user information
        if make_new_students:
            production = gns.config.defaults.production
            if production:
                users = [item[4] for item in pwd.getpwall()]
                # TODO: Use the home in settings.ini
                path_to_script = gns.config.directories.path_to_newstudent_script
                write_user = lambda x: ["/bin/bash", path_to_script, x.idnumber, x.username, "'{}'".format(x.lastfirst)]
            else:
                path_to_users = gns.config.directories.path_to_users
                users = os.listdir(path_to_users)
                write_user = lambda x: ['touch', '{}/{}'.format(path_to_users, x.idnumber)]

            check_users = lambda x: x.idnumber in users

        for student_key in self.students.get_keys():
            student = self.students.get_key(student_key)

            # We need to check the dragonnet database for the email address
            # Because we don't have a way otherwise

            with DBSession() as session:
                try:
                    in_dragonnet = session.query(User).filter_by(idnumber=student.idnumber).one()
                    if in_dragonnet.email != student.email:
                        student.username = in_dragonnet.username
                        student.email = in_dragonnet.email
                except NoResultFound, MultipleResultsFound:
                    pass 

            if make_new_students:
                if student.grade >= 4 and not check_users(student):
                    self.logger.warning("Making new student email {}".format(student))
                    subprocess.call(write_user(student))

            # TODO: Check for now grade or homeroom and warn
            if student.grade is "" or student.grade is None:
                self.logger.warn("This student does not have a grade:\n{}".format(student))
            if not student.homeroom:
                self.logger.warn("This student does not have a homeroom:\n{}".format(student))

            this_grade = student.grade
            # USE ns.grade BECAUSE student.grade IS AN INTEGER
            # TODO: DO WE MAKE student.grade A STRING?
            # OR PUT THIS IN THE OBJECT SOMEWHOW?
            if student.grade <= 0:
                this_grade = {0: 'K', -1: 'PK', -2: 'N', -3:'PN'}.get(this_grade, 'None')

            self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsALL)
            self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsGRADE(this_grade))
            self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsHROOM(student.homeroom))

            if student.is_elementary:
                if student.grade >= 4:
                    self.bm.add_email(student.email, self.bm.cat.global_, self.bm.studentsGRADE(student.grade))
                    for group in student.groups:
                        self.bm.add_email(student.email, self.bm.cat.classes, self.bm.groups(group.idnumber))
                        self.bm.add_email(student.email, self.bm.cat.classes, self.bm.groupsPARENTS(group.idnumber))

                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsELEM)
                self.bm.add_emails(student.guardian_emails, self.bm.cat.parentlink, self.bm.parentlink(student.username))
                self.bm.add_emails(student.teacher_emails, self.bm.cat.teacherlink, self.bm.teacherlink(student.username))
                self.bm.add_email(student.homeroom_teacher_email, self.bm.cat.homeroomlink, self.bm.hrlink(student.username))

            if student.is_secondary:
                self.bm.add_email(student.email, self.bm.cat.global_, self.bm.studentsSEC)
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsSEC)

                if this_grade:
                    self.bm.add_email(student.email, self.bm.cat.grades, self.bm.studentsGRADE(this_grade))
                    self.bm.add_emails(student.teacher_emails, self.bm.cat.grades, self.bm.teachersGRADE(this_grade))

                if student.homeroom:
                    self.bm.add_email(student.email, self.bm.cat.homerooms, self.bm.studentsHOMEROOM(student.homeroom))

                self.bm.add_emails(student.guardian_emails, self.bm.cat.parentlink, self.bm.parentlink(student.username))
                self.bm.add_emails(student.teacher_emails, self.bm.cat.teacherlink, self.bm.teacherlink(student.username))
                self.bm.add_email(student.homeroom_teacher_email, self.bm.cat.homeroomlink, self.bm.hrlink(student.username))

                for group in student.groups:
                    self.bm.add_email(student.email, self.bm.cat.classes, self.bm.groups(group.idnumber))
                    self.bm.add_emails(student.guardian_emails, self.bm.cat.classes, self.bm.groupsPARENTS(group.idnumber))

            if student.is_chinese and not excluded_from_chinese_list(student):
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsCHINESE)
                student.is_secondary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsCHINESESEC)
                student.is_elementary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsCHINESEELEM)
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsCHINESEGRADE(this_grade))

            if student.is_korean:
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsKOREAN)
                student.is_secondary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsKOREANSEC)
                student.is_elementary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsKOREANELEM)
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsKOREANGRADE(this_grade))

            if student.is_japanese:
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsJAPANESE)
                student.is_secondary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsJAPANESESEC)
                student.is_elementary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsJAPANESEELEM)
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsJAPANESEGRADE(this_grade))

            if student.is_german:
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsGERMAN)
                student.is_secondary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsGERMANSEC)
                student.is_elementary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsGERMANELEM)
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsGERMANGRADE(this_grade))
            else:
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsNOTGERMAN)

            if student.is_SWA:
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsSWA)
                student.is_secondary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsSWASEC)
                student.is_elementary and self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsSWAELEM)
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsSWAGRADE(this_grade))
            else:
                self.bm.add_emails(student.guardian_emails, self.bm.cat.global_, self.bm.parentsNOTSWA)

        # Manually add them ... Boo
        kor_president = 'greenmarch11@naver.com'
        self.bm.add_email(kor_president, self.bm.cat.global_, self.bm.parentsELEM)
        self.bm.add_email(kor_president, self.bm.cat.global_, self.bm.parentsKOREAN)
        self.bm.add_email(kor_president, self.bm.cat.global_, self.bm.parentsKOREANSEC)
        self.bm.add_email(kor_president, self.bm.cat.global_, self.bm.parentsKOREANELEM)


        # Secondary Activities
        # Gets all the students that are enrolled as self (or meta, why meta, because they use that for enrollments)
        # That is in the activities category
        with DBSession() as session:
             results = session.query(
                Course.fullname, User.idnumber
             ).\
             select_from(Enrol).\
             join(UserEnrolment, UserEnrolment.enrolid == Enrol.id).\
             join(Course, Enrol.courseid == Course.id).\
             join(CourseCategory, CourseCategory.id == Course.category).\
             join(User, UserEnrolment.userid == User.id).filter(
                and_(
                    CourseCategory.path.like('/1/%'),
                    not_(User.idnumber.like('%P')),
                    or_(
                        Enrol.enrol == 'self_parents',
                        Enrol.enrol == 'meta'
                        )
                )).all()

        for result in results:
            activity_name, student_key = result
            student = self.students.get_key(student_key)
            if not student:
                self.logger.info('This student enrolled into activity, ' + \
                                    'but has left. Ignored. {}'.format(student_key))
                continue
            normalized_name = name_to_email(activity_name)
            if not normalized_name:
                continue
            self.bm.add_email(student.email, self.bm.cat.activities, normalized_name+'ACT')
            self.bm.add_emails(student.guardian_emails, self.bm.cat.activities, normalized_name+'ACTPARENTS')




