from psmdlsyncer.models.datastores.tree import AbstractTree
from psmdlsyncer.files import AutoSendImport
from psmdlsyncer.models.datastores.branch import DataStore
from psmdlsyncer.settings import config, config_get_section_attribute
from psmdlsyncer.utils import NS2
from psmdlsyncer.files import clear_folder
from collections import defaultdict
from psmdlsyncer.db import DBSession
from psmdlsyncer.db.MoodleDB import *
from sqlalchemy.orm.exc import NoResultFound
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
        where = -1
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
                except NoResultFound:
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
                this_grade = {0: 'K', -1: 'R', -2: 'G', -3:'PK', -4:'N'}.get(this_grade, None)

            bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsALL)
            bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsGRADE(this_grade))
            bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsHROOM(student.homeroom))

            if student.is_elementary:
                if student.grade >= 4:
                    bm.add_email(student.email, bm.cat.global_, bm.studentsGRADE(student.grade))
                    for group in student.groups:
                        bm.add_email(student.email, bm.cat.classes, bm.groups(group.name))
                        bm.add_email(student.email, bm.cat.classes, bm.groupsPARENTS(group.name))

                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsELEM)
                bm.add_emails(student.guardian_emails, bm.cat.parentlink, bm.parentlink(student.username))
                bm.add_emails(student.guardian_emails, bm.cat.teacherlink, bm.teacherlink(student.username))
                bm.add_emails(student.guardian_emails, bm.cat.homeroomlink, bm.hrlink(student.username))

            if student.is_secondary:
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsSEC)
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.studentsSEC)

                if this_grade:
                    bm.add_email(student.email, bm.cat.grades, bm.studentsGRADE(this_grade))
                    bm.add_emails(student.teacher_emails, bm.cat.grades, bm.teachersGRADE(this_grade))

                if student.homeroom:
                    bm.add_email(student.email, bm.cat.homerooms, bm.studentsHOMEROOM(student.homeroom))

                bm.add_emails(student.guardian_emails, bm.cat.parentlink, bm.parentlink(student.username))
                bm.add_emails(student.teacher_emails, bm.cat.teacherlink, bm.teacherlink(student.username))
                bm.add_email(student.homeroom_teacher_email, bm.cat.homeroomlink, bm.hrlink(student.username))

                for group in student.groups:
                    bm.add_email(student.email, bm.cat.classes, bm.groups(group.name))
                    bm.add_emails(student.guardian_emails, bm.cat.classes, bm.groupsPARENTS(group.name))

            if student.is_chinese and not excluded_from_chinese_list(student):
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsCHINESE)
                student.is_secondary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsCHINESESEC)
                student.is_elementary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsCHINESEELEM)
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsCHINESEGRADE(this_grade))

            if student.is_korean:
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsKOREAN)
                student.is_secondary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsKOREANSEC)
                student.is_elementary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsKOREANELEM)
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsKOREANGRADE(this_grade))

            if student.is_japanese:
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsJAPANESE)
                student.is_secondary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsJAPANESESEC)
                student.is_elementary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsJAPANESEELEM)
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsJAPANESEGRADE(this_grade))

            if student.is_german:
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsGERMAN)
                student.is_secondary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsGERMANSEC)
                student.is_elementary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsGERMANELEM)
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsGERMANGRADE(this_grade))
            else:
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsNOTGERMAN)

            if student.is_SWA:
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsSWA)
                student.is_secondary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsSWASEC)
                student.is_elementary and bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsSWAELEM)
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsSWAGRADE(this_grade))
            else:
                bm.add_emails(student.guardian_emails, bm.cat.global_, bm.parentsNOTSWA)

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
             join(User, UserEnrolment.userid == User.id).filter(
                and_(
                    not_(User.idnumber.like('%P')),
                    or_(
                        Enrol.enrol == 'self',
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
            bm.add_email(student.email, bm.cat.activities, normalized_name)
            bm.add_emails(student.guardian_emails, bm.cat.activities+"ACT", normalized_name+'ACTPARENTS')




