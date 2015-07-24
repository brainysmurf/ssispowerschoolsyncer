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

    def build_automagic_emails(self):

        bm = BulkEmailManager()

        self.logger.debug("Setting email lists")

        # Set up the user information

        # production = gns.config.defaults.production
        # if production:
        #     users = [item[4] for item in pwd.getpwall()]
        #     # TODO: Use the home in settings.ini
        #     path_to_script = gns.config.directories.path_to_newstudent_script
        #     write_user = lambda x: ["/bin/bash", path_to_script, x.idnumber, x.username, "'{}'".format(x.lastfirst)]
        # else:
        #     path_to_users = gns.config.directories.path_to_users
        #     users = os.listdir(path_to_users)
        #     write_user = lambda x: ['touch', '{}/{}'.format(path_to_users, x.idnumber)]

        # check_users = lambda x: x.idnumber in users

        # Loop through all the students, baby

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

            # if student.grade >= 4 and not check_users(student):
            #     self.logger.warning("Making new student email {}".format(student))
            #     subprocess.call(write_user(student))

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

        bm.output_all()
        exit()

        # # GRADES
        # directory_write = []
        # for ns.grade in usebccparentsGRADE:
        #     directory_write.append( ns('usebccparents{grade}{COLON}{INCLUDE}{PATH}{SLASH}grades{SLASH}usebccparents{grade}{EXT}') )
        #     with open( ns('{PATH}{SLASH}grades{SLASH}usebccparents{grade}{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(usebccparentsGRADE[ns.grade])) )
        # for ns.grade in usebccstudentsGRADE:
        #     directory_write.append( ns('usebccstudents{grade}{COLON}{INCLUDE}{PATH}{SLASH}grades{SLASH}usebccstudents{grade}{EXT}') )
        #     with open( ns('{PATH}{SLASH}grades{SLASH}usebccstudents{grade}{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(usebccstudentsGRADE[ns.grade])) )
        # for ns.grade in teachersGRADE:
        #     directory_write.append( ns('teachers{grade}{COLON}{INCLUDE}{PATH}{SLASH}grades{SLASH}teachers{grade}{EXT}') )
        #     with open( ns('{PATH}{SLASH}grades{SLASH}teachers{grade}{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(teachersGRADE[ns.grade])) )
        # with open( ns('{PATH}{SLASH}grades{EXT}'), 'w') as f:
        #     f.write( '\n'.join(directory_write) )

        #     #HS

        # # HOMEROOMS
        # directory_write = []
        # for ns.homeroom in self.usebccparentsHOMEROOM:
        #     directory_write.append( ns('usebccparents{homeroom}{COLON}{INCLUDE}{PATH}{SLASH}homerooms{SLASH}usebccparents{homeroom}{EXT}') )
        #     with open( ns('{PATH}{SLASH}homerooms{SLASH}usebccparents{homeroom}{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(self.usebccparentsHOMEROOM[ns.homeroom])) )
        # for ns.homeroom in self.usebccstudentsHOMEROOM:
        #     directory_write.append( ns('usebccstudents{homeroom}{COLON}{INCLUDE}{PATH}{SLASH}homerooms{SLASH}usebccstudents{homeroom}{EXT}') )
        #     with open( ns('{PATH}{SLASH}homerooms{SLASH}usebccstudents{homeroom}{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(self.usebccstudentsHOMEROOM[ns.homeroom])) )
        # with open( ns('{PATH}{SLASH}homerooms{EXT}'), 'w') as f:
        #     f.write( '\n'.join(directory_write) )

        # # TEACHERLINK
        # directory_write = []
        # for ns.student in teacherlink:
        #     directory_write.append( ns('{student}TEACHERS{COLON}{INCLUDE}{PATH}{SLASH}teacherlink{SLASH}{student}TEACHERS{EXT}') )
        #     with open( ns('{PATH}{SLASH}teacherlink{SLASH}{student}TEACHERS{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(teacherlink[ns.student])) )
        # with open( ns('{PATH}{SLASH}teacherlink{EXT}'), 'w') as f:
        #     f.write( '\n'.join(directory_write) )

        # # PARENTLINK
        # directory_write = []
        # for ns.student in parentlink:
        #     directory_write.append( ns('{student}PARENTS{COLON}{INCLUDE}{PATH}{SLASH}parentlink{SLASH}{student}PARENTS{EXT}') )
        #     with open( ns('{PATH}{SLASH}parentlink{SLASH}{student}PARENTS{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(parentlink[ns.student])) )
        # with open( ns('{PATH}{SLASH}parentlink{EXT}'), 'w') as f:
        #     f.write( '\n'.join(directory_write) )

        # # HRLINK
        # directory_write = []
        # for ns.student in hrlink:
        #     if hrlink[ns.student]:  # not all kids have a homeroom teacher....
        #         directory_write.append( ns('{student}HR{COLON}{INCLUDE}{PATH}{SLASH}homeroomlink{SLASH}{student}HR{EXT}') )
        #         with open( ns('{PATH}{SLASH}homeroomlink{SLASH}{student}HR{EXT}'), 'w') as f:
        #             try:
        #                 f.write( '\n'.join(set(hrlink[ns.student])) )
        #             except TypeError:
        #               pass

        # with open( ns('{PATH}{SLASH}homeroomlink{EXT}'), 'w') as f:
        #     f.write( '\n'.join(directory_write) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsALL{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsALL) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsSEC{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsSEC) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccstudentsALL{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccstudentsALL) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccstudentsSEC{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccstudentsSEC) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsELEM{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsELEM) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESE{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsCHINESE) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESESEC{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsCHINESESEC) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESEELEM{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsCHINESEELEM) )

        # for ns.grade in usebccparentsCHINESEGRADE:
        #     with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESE{grade}{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(usebccparentsCHINESEGRADE[ns.grade])) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREAN{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsKOREAN) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREANELEM{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsKOREANSEC) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREANSEC{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsKOREANSEC) )

        # for ns.grade in usebccparentsKOREANGRADE:
        #     with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREAN{grade}{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(usebccparentsKOREANGRADE[ns.grade])) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsJAPANESE{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsJAPANESE) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsJAPANESESEC{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsJAPANESESEC) )

        # for ns.grade in usebccparentsJAPANESEGRADE:
        #     with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsJAPANESE{grade}{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(usebccparentsJAPANESEGRADE[ns.grade])) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsSWA{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsSWA) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsNOTSWA{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsNOTSWA) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsGERMAN{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsGERMAN) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsNOTGERMAN{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccparentsNOTGERMAN) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccstudentsSWA{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccstudentsSWA) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccstudentsALL{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccstudentsALL) )

        # with open( ns('{PATH}{SLASH}special{SLASH}usebccstudentsSEC{EXT}'), 'w') as f:
        #     f.write( '\n'.join(usebccstudentsSEC) )

        # with open( ns('{PATH}{SLASH}special{SLASH}koreanstudentsSEC{EXT}'), 'w') as f:
        #     f.write( '\n'.join(koreanstudentsSEC) )

        # with open( ns('{PATH}{SLASH}special{SLASH}chinesestudentsSEC{EXT}'), 'w') as f:
        #     f.write( '\n'.join(chinesestudentsSEC) )

        # with open( ns('{PATH}{SLASH}special{EXT}'), 'w') as f:
        #     for ns.this in ['usebccparentsALL', 'usebccparentsSEC', 'usebccstudentsALL', 'usebccstudentsSEC', 'usebccparentsELEM',
        #                     'usebccparentsKOREAN', 'usebccparentsKOREANSEC', 'usebccparentsKOREANELEM',
        #                     'usebccparentsCHINESE', 'usebccparentsCHINESESEC', 'usebccparentsCHINESEELEM',
        #                     'usebccparentsJAPANESE', 'usebccparentsJAPANESESEC', 'usebccparentsJAPANESEELEM',
        #                     'usebccparentsSWA', 'usebccstudentsSWA', 'usebccparentsNOTSWA', 'usebccparentsNOTGERMAN', 'usebccparentsGERMAN', 'koreanstudentsSEC', 'chinesestudentsSEC']:
        #         f.write( ns('{this}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}{this}{EXT}{NEWLINE}') )
        #     for ns.grade in usebccparentsKOREANGRADE:
        #         f.write( ns('usebccparentsKOREAN{grade}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparentsKOREAN{grade}{EXT}{NEWLINE}') )
        #     for ns.grade in usebccparentsCHINESEGRADE:
        #         f.write( ns('usebccparentsCHINESE{grade}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparentsCHINESE{grade}{EXT}{NEWLINE}') )
        #     for ns.grade in usebccparentsJAPANESEGRADE:
        #         f.write( ns('usebccparentsJAPANESE{grade}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparentsJAPANESE{grade}{EXT}{NEWLINE}') )

        # # CLASSES
        # directory_write = []
        # for ns.klass in classes:
        #     directory_write.append( ns('{klass}{COLON}{INCLUDE}{PATH}{SLASH}classes{SLASH}{klass}{EXT}') )
        # for ns.klass in classesPARENTS:
        #     directory_write.append( ns('{klass}PARENTS{COLON}{INCLUDE}{PATH}{SLASH}classes{SLASH}{klass}PARENTS{EXT}') )
        # with open( ns('{PATH}{SLASH}classes{EXT}'), 'w') as f:
        #     f.write( '\n'.join(directory_write) )

        # for ns.klass in classes:
        #     with open( ns('{PATH}{SLASH}classes{SLASH}{klass}{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(classes[ns.klass])) )

        # for ns.klass in classesPARENTS:
        #     with open( ns('{PATH}{SLASH}classes{SLASH}{klass}PARENTS{EXT}'), 'w') as f:
        #         f.write( '\n'.join(set(classesPARENTS[ns.klass])) )


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

        ns = NS2()
        ns.domain = 'student.ssis-suzhou.net'
        activities_postfix = defaultdict(list)
        activities_postfix_parents = defaultdict(list)
        for result in results:
            activity_name, student_key = result
            student = self.students.get_key(student_key)
            if not student:
                self.logger.info('This student enrolled into activity, ' + \
                                    'but has left. Ignored. {}'.format(student_key))
                continue
            activities_postfix[activity_name].append(student.email)
            activities_postfix_parents[activity_name].append(student.parent_link_email)

        # DO THE ACTIVITY EMAILS
        ns.path = gns.config.directories.path_to_postfix
        ns.base = 'activities'
        ns.SUFFIX = "ACT"
        ns.EXT = '.txt'
        ns.INCLUDE = ':include:'
        ns.activities_path = ns('{path}{SLASH}activities')
        with open(ns('{path}{SLASH}{base}{EXT}'), 'w'):
            pass

        for activity_name in activities_postfix:
            
            ns.handle = name_to_email(activity_name)
            ns.full_email = ns('{handle}{SUFFIX}')
            if ns.handle == ns('{SUFFIX}'):
                continue
            with open(ns('{path}{SLASH}{base}{EXT}'), 'a') as f:
                f.write(ns('{full_email}{COLON}{SPACE}{INCLUDE}' + \
                           '{activities_path}{SLASH}{full_email}{EXT}{NEWLINE}'))
            with open(ns('{activities_path}{SLASH}{full_email}{EXT}'), 'a') as f:
                f.write("\n".join(activities_postfix[activity_name]))

        ns.SUFFIX = "ACTPARENTS"
        for activity_name in activities_postfix_parents:
            ns.handle = name_to_email(activity_name)
            ns.full_email = ns('{handle}{SUFFIX}')
            if ns.handle == ns('{SUFFIX}'):
                continue
            with open(ns('{path}{SLASH}{base}{EXT}'), 'a') as f:
                f.write(ns('{full_email}{COLON}{SPACE}{INCLUDE}' + \
                           '{activities_path}{SLASH}{full_email}{EXT}{NEWLINE}'))
            with open(ns('{activities_path}{SLASH}{full_email}{EXT}'), 'a') as f:
                f.write("\n".join(activities_postfix_parents[activity_name]))

        # run newaliases command on exit if we're on the server
        newaliases_path = gns.config.email.newaliases_path
        if newaliases_path:
            self.logger.info("Running newaliases")
            p = subprocess.Popen(newaliases_path, shell=True)
            self.logger.info(p.communicate())
        else:
            self.logger.warn("newaliases not run!")
        #TODO: If received error, should email admin
