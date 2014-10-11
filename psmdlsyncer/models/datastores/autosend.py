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

class AutoSendTree(AbstractTree):
    pickup = DataStore
    klass = AutoSendImport
    convert_course = True

    def process_mrbs_editor(self):
        for teacher in self.teachers.get_objects():
            self.mrbs_editor.make(teacher.ID)

    def build_automagic_emails(self):
        path = config_get_section_attribute('DIRECTORIES', 'path_to_postfix')

        ns = NS2()
        ns.PATH = path
        ns.EXT = '.txt'
        ns.INCLUDE = ' :include:'

        # The clear_folder routine erases all files in a certain folder
        # That has implications for postfix (when we're on the server), because
        # if you delete the .db files then postfix won't work. That is bad.
        # So, tell clear_folder to exclude them
        exclude_db_files = lambda x: x.endswith('.db')
        self.logger.debug("Clearing folders in postfix")
        clear_folder( ns.PATH, exclude=exclude_db_files)
        clear_folder(ns('{PATH}/grades'))
        clear_folder(ns('{PATH}/homerooms'))
        clear_folder(ns('{PATH}/classes'))
        clear_folder(ns('{PATH}/parentlink'))
        clear_folder(ns('{PATH}/teacherlink'))
        clear_folder(ns('{PATH}/homeroomlink'))
        clear_folder(ns('{PATH}/special'))
        clear_folder(ns('{PATH}/departments'))
        clear_folder(ns('{PATH}/activities'))

        special_directory = []

        self.logger.debug("Setting up largest mailing lists first")

        for item in ['ALL', 'SEC', 'ELEM', 'KOREAN', 'CHINESE']:
            ns.this = item
            special_directory.append( ns('usebccparents{this}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparents{this}{EXT}') )

        with open( ns('{PATH}/special{EXT}'), 'w') as f:
            f.write( "\n".join(special_directory) )

        usebccparentsALL = []
        usebccstudentsALL = []
        usebccparentsELEM = []
        usebccparentsSEC = []
        usebccstudentsSEC = []
        koreanstudentsSEC = []
        chinesestudentsSEC = []
        usebccparentsCHINESE = []
        usebccparentsCHINESEELEM = []
        usebccparentsCHINESESEC = []
        usebccparentsCHINESEGRADE = defaultdict(list)
        usebccparentsKOREAN = []
        usebccparentsKOREANELEM = []
        usebccparentsKOREANSEC = []
        usebccparentsKOREANGRADE = defaultdict(list)
        usebccparentsJAPANESE = []
        usebccparentsJAPANESEELEM = []
        usebccparentsJAPANESESEC = []
        usebccparentsJAPANESEGRADE = defaultdict(list)
        # SWA DISTRIBUTION LISTS
        usebccparentsSWA = []
        usebccstudentsSWA = []
        usebccparentsNOTSWA = []
        usebccparentsSWAGRADE = defaultdict(list)
        usebccstudentsSWAGRADE = defaultdict(list)
        usebccparentsGERMAN = []
        usebccparentsNOTGERMAN = []
        # HR AND GRADE
        usebccparentsHOMEROOM = defaultdict(list)
        usebccparentsGRADE = defaultdict(list)
        usebccparentsHOMEROOM = defaultdict(list)
        usebccstudentsELEM = defaultdict(list)
        usebccstudentsGRADE = defaultdict(list)
        usebccstudentsHOMEROOM = defaultdict(list)
        parentlink = defaultdict(list)
        teacherlink = defaultdict(list)
        teachersGRADE = defaultdict(list)
        hrlink = defaultdict(list)
        classes = defaultdict(list)
        classesPARENTS = defaultdict(list)
        special = defaultdict(list)

        self.logger.debug("Setting email lists")

        # Set up the user information

        production = config_get_section_attribute('DEFAULTS', 'production')
        if production:
            users = [item[4] for item in pwd.getpwall()]
            # TODO: Use the home in settings.ini
            path_to_script = config_get_section_attribute('DIRECTORIES', 'path_to_newstudent_script')
            write_user = lambda x: ["/bin/bash", path_to_script, x.idnumber, x.username, "'{}'".format(x.lastfirst)]
        else:
            path_to_users = config_get_section_attribute('DIRECTORIES', 'path_to_users')
            users = os.listdir(path_to_users)
            write_user = lambda x: ['touch', '{}/{}'.format(path_to_users, x.idnumber)]

        check_users = lambda x: x.idnumber in users

        # Loop through all the students, baby

        for student_key in self.students.get_keys():
            student = self.students.get_key(student_key)

            # We need to check the dragonnet database for the email address
            # Because we don't have a way otherwise

            with DBSession() as session:
                try:
                    in_dragonnet = session.query(User).filter_by(idnumber=student.idnumber).one()
                    if in_dragonnet.email != student.email:
                        student.email = in_dragonnet.email
                except NoResultFound:
                    pass

            if student.grade >= 4 and not check_users(student):
                self.logger.warning("Making new student email {}".format(student))
                subprocess.call(write_user(student))

            ns.homeroom = student.homeroom
            ns.grade = student.grade

            # TODO: Check for now grade or homeroom and warn
            if student.grade is "" or student.grade is None:
                self.logger.warn("This student does not have a grade:\n{}".format(student))
            if not student.homeroom:
                self.logger.warn("This student does not have a homeroom:\n{}".format(student))

            # USE ns.grade BECAUSE student.grade IS AN INTEGER
            # TODO: DO WE MAKE student.grade A STRING?
            # OR PUT THIS IN THE OBJECT SOMEWHOW?
            if ns.grade <= 0:
                ns.grade = {0: 'K', -1: 'R', -2: 'G', -3:'PK', -4:'N'}.get(ns.grade, None)

            usebccparentsALL.extend( student.guardian_emails )
            ns.grade and usebccparentsGRADE[ns.grade].extend(student.guardian_emails)
            ns.homeroom and usebccparentsHOMEROOM[ns.homeroom].extend(student.guardian_emails)

            if student.is_elementary:
                if student.grade >= 4:
                    usebccstudentsGRADE[student.grade].append(student.email)
                    for group in student.groups:
                        classes[group.name].append(student.email)
                        classesPARENTS[group.name].extend(student.guardian_emails)

                usebccparentsELEM.extend(student.guardian_emails)
                parentlink[student.username].extend( student.guardian_emails )
                teacherlink[student.username].extend(student.teacher_emails)
                hrlink[student.username].append(student.homeroom_teacher_email)

            if student.is_secondary:
                usebccparentsSEC.extend(student.guardian_emails)
                usebccstudentsSEC.append(student.email)
                if ns.grade:
                    usebccstudentsGRADE[ns.grade].append(student.email)
                    teachersGRADE[ns.grade].extend(student.teacher_emails)
                if student.homeroom:
                    usebccstudentsHOMEROOM[ns.homeroom].append(student.email)
                parentlink[student.username].extend( student.guardian_emails )
                teacherlink[student.username].extend(student.teacher_emails)
                hrlink[student.username].append(student.homeroom_teacher_email)
                for group in student.groups:
                    classes[group.name].append(student.email)
                    classesPARENTS[group.name].extend(student.guardian_emails)

                if student.is_korean:
                    koreanstudentsSEC.append( student.email )
                if student.is_chinese:
                    chinesestudentsSEC.append( student.email )

            if student.is_chinese and not excluded_from_chinese_list(student):
                usebccparentsCHINESE.extend( student.guardian_emails )
                student.is_secondary and usebccparentsCHINESESEC.extend( student.guardian_emails )
                student.is_elementary and usebccparentsCHINESEELEM.extend( student.guardian_emails )
                usebccparentsCHINESEGRADE[ns.grade].extend( student.guardian_emails )
            if student.is_korean:
                usebccparentsKOREAN.extend( student.guardian_emails )
                student.is_secondary and usebccparentsKOREANSEC.extend( student.guardian_emails )
                student.is_elementary and usebccparentsKOREANELEM.extend( student.guardian_emails )
                usebccparentsKOREANGRADE[ns.grade].extend( student.guardian_emails )
            if student.is_japanese:
                usebccparentsJAPANESE.extend( student.guardian_emails )
                student.is_secondary and usebccparentsJAPANESESEC.extend( student.guardian_emails )
                student.is_elementary and usebccparentsJAPANESEELEM.extend( student.guardian_emails )
                usebccparentsJAPANESEGRADE[ns.grade].extend( student.guardian_emails )
            if student.is_german:
                usebccparentsGERMAN.extend( student.guardian_emails )
            else:
                usebccparentsNOTGERMAN.extend( student.guardian_emails )
            if student.is_SWA:
                usebccparentsSWA.extend( student.guardian_emails )
                usebccstudentsSWA.append( student.email )
                usebccparentsSWAGRADE[ns.grade].extend( student.guardian_emails )
                usebccstudentsSWAGRADE[ns.grade].append( student.email )
            else:
                usebccparentsNOTSWA.extend( student.guardian_emails )

        # GRADES
        directory_write = []
        for ns.grade in usebccparentsGRADE:
            directory_write.append( ns('usebccparents{grade}{COLON}{INCLUDE}{PATH}{SLASH}grades{SLASH}usebccparents{grade}{EXT}') )
            with open( ns('{PATH}{SLASH}grades{SLASH}usebccparents{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsGRADE[ns.grade])) )
        for ns.grade in usebccstudentsGRADE:
            directory_write.append( ns('usebccstudents{grade}{COLON}{INCLUDE}{PATH}{SLASH}grades{SLASH}usebccstudents{grade}{EXT}') )
            with open( ns('{PATH}{SLASH}grades{SLASH}usebccstudents{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccstudentsGRADE[ns.grade])) )
        for ns.grade in teachersGRADE:
            directory_write.append( ns('teachers{grade}{COLON}{INCLUDE}{PATH}{SLASH}grades{SLASH}teachers{grade}{EXT}') )
            with open( ns('{PATH}{SLASH}grades{SLASH}teachers{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(teachersGRADE[ns.grade])) )
        with open( ns('{PATH}{SLASH}grades{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

            #HS

        # HOMEROOMS
        directory_write = []
        for ns.homeroom in usebccparentsHOMEROOM:
            directory_write.append( ns('usebccparents{homeroom}{COLON}{INCLUDE}{PATH}{SLASH}homerooms{SLASH}usebccparents{homeroom}{EXT}') )
            with open( ns('{PATH}{SLASH}homerooms{SLASH}usebccparents{homeroom}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsHOMEROOM[ns.homeroom])) )
        for ns.homeroom in usebccstudentsHOMEROOM:
            directory_write.append( ns('usebccstudents{homeroom}{COLON}{INCLUDE}{PATH}{SLASH}homerooms{SLASH}usebccstudents{homeroom}{EXT}') )
            with open( ns('{PATH}{SLASH}homerooms{SLASH}usebccstudents{homeroom}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccstudentsHOMEROOM[ns.homeroom])) )
        with open( ns('{PATH}{SLASH}homerooms{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        # TEACHERLINK
        directory_write = []
        for ns.student in teacherlink:
            directory_write.append( ns('{student}TEACHERS{COLON}{INCLUDE}{PATH}{SLASH}teacherlink{SLASH}{student}TEACHERS{EXT}') )
            with open( ns('{PATH}{SLASH}teacherlink{SLASH}{student}TEACHERS{EXT}'), 'w') as f:
                f.write( '\n'.join(set(teacherlink[ns.student])) )
        with open( ns('{PATH}{SLASH}teacherlink{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        # PARENTLINK
        directory_write = []
        for ns.student in parentlink:
            directory_write.append( ns('{student}PARENTS{COLON}{INCLUDE}{PATH}{SLASH}parentlink{SLASH}{student}PARENTS{EXT}') )
            with open( ns('{PATH}{SLASH}parentlink{SLASH}{student}PARENTS{EXT}'), 'w') as f:
                f.write( '\n'.join(set(parentlink[ns.student])) )
        with open( ns('{PATH}{SLASH}parentlink{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        # HRLINK
        directory_write = []
        for ns.student in hrlink:
            if hrlink[ns.student]:  # not all kids have a homeroom teacher....
                directory_write.append( ns('{student}HR{COLON}{INCLUDE}{PATH}{SLASH}homeroomlink{SLASH}{student}HR{EXT}') )
                with open( ns('{PATH}{SLASH}homeroomlink{SLASH}{student}HR{EXT}'), 'w') as f:
                    try:
                        f.write( '\n'.join(set(hrlink[ns.student])) )
                    except TypeError:
                      pass
        with open( ns('{PATH}{SLASH}homeroomlink{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsALL{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsALL) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsSEC{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsSEC) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsELEM{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsELEM) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESE{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsCHINESE) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESESEC{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsCHINESESEC) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESEELEM{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsCHINESEELEM) )

        for ns.grade in usebccparentsCHINESEGRADE:
            with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsCHINESE{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsCHINESEGRADE[ns.grade])) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREAN{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsKOREAN) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREANELEM{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsKOREANSEC) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREANSEC{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsKOREANSEC) )

        for ns.grade in usebccparentsKOREANGRADE:
            with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsKOREAN{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsKOREANGRADE[ns.grade])) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsJAPANESE{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsJAPANESE) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsJAPANESESEC{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsJAPANESESEC) )

        for ns.grade in usebccparentsJAPANESEGRADE:
            with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsJAPANESE{grade}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(usebccparentsJAPANESEGRADE[ns.grade])) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsSWA{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsSWA) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsNOTSWA{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsNOTSWA) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsGERMAN{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsGERMAN) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccparentsNOTGERMAN{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccparentsNOTGERMAN) )

        with open( ns('{PATH}{SLASH}special{SLASH}usebccstudentsSWA{EXT}'), 'w') as f:
            f.write( '\n'.join(usebccstudentsSWA) )

        with open( ns('{PATH}{SLASH}special{SLASH}koreanstudentsSEC{EXT}'), 'w') as f:
            f.write( '\n'.join(koreanstudentsSEC) )

        with open( ns('{PATH}{SLASH}special{SLASH}chinesestudentsSEC{EXT}'), 'w') as f:
            f.write( '\n'.join(chinesestudentsSEC) )

        with open( ns('{PATH}{SLASH}special{EXT}'), 'w') as f:
            for ns.this in ['usebccparentsALL', 'usebccparentsSEC', 'usebccparentsELEM',
                            'usebccparentsKOREAN', 'usebccparentsKOREANSEC', 'usebccparentsKOREANELEM',
                            'usebccparentsCHINESE', 'usebccparentsCHINESESEC', 'usebccparentsCHINESEELEM',
                            'usebccparentsJAPANESE', 'usebccparentsJAPANESESEC', 'usebccparentsJAPANESEELEM',
                            'usebccparentsSWA', 'usebccstudentsSWA', 'usebccparentsNOTSWA', 'usebccparentsNOTGERMAN', 'usebccparentsGERMAN', 'koreanstudentsSEC', 'chinesestudentsSEC']:
                f.write( ns('{this}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}{this}{EXT}{NEWLINE}') )
            for ns.grade in usebccparentsKOREANGRADE:
                f.write( ns('usebccparentsKOREAN{grade}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparentsKOREAN{grade}{EXT}{NEWLINE}') )
            for ns.grade in usebccparentsCHINESEGRADE:
                f.write( ns('usebccparentsCHINESE{grade}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparentsCHINESE{grade}{EXT}{NEWLINE}') )
            for ns.grade in usebccparentsJAPANESEGRADE:
                f.write( ns('usebccparentsJAPANESE{grade}{COLON}{INCLUDE}{PATH}{SLASH}special{SLASH}usebccparentsJAPANESE{grade}{EXT}{NEWLINE}') )

        # CLASSES
        directory_write = []
        for ns.klass in classes:
            directory_write.append( ns('{klass}{COLON}{INCLUDE}{PATH}{SLASH}classes{SLASH}{klass}{EXT}') )
        for ns.klass in classesPARENTS:
            directory_write.append( ns('{klass}PARENTS{COLON}{INCLUDE}{PATH}{SLASH}classes{SLASH}{klass}PARENTS{EXT}') )
        with open( ns('{PATH}{SLASH}classes{EXT}'), 'w') as f:
            f.write( '\n'.join(directory_write) )

        for ns.klass in classes:
            with open( ns('{PATH}{SLASH}classes{SLASH}{klass}{EXT}'), 'w') as f:
                f.write( '\n'.join(set(classes[ns.klass])) )

        for ns.klass in classesPARENTS:
            with open( ns('{PATH}{SLASH}classes{SLASH}{klass}PARENTS{EXT}'), 'w') as f:
                f.write( '\n'.join(set(classesPARENTS[ns.klass])) )


        # Secondary Activities
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
                self.logger.warning('This student enrolled into activity, ' + \
                                    'but has left. Ignored. {}'.format(student_key))
                continue
            activities_postfix[activity_name].append(student.email)
            activities_postfix_parents[activity_name].append(student.parent_link_email)

        # DO THE ACTIVITY EMAILS
        ns.path = config_get_section_attribute('DIRECTORIES', 'path_to_postfix')
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
            with open(ns('{path}{SLASH}{base}{EXT}'), 'a') as f:
                f.write(ns('{full_email}{COLON}{SPACE}{INCLUDE}' + \
                           '{activities_path}{SLASH}{full_email}{EXT}{NEWLINE}'))
            with open(ns('{activities_path}{SLASH}{full_email}{EXT}'), 'a') as f:
                f.write("\n".join(activities_postfix[activity_name]))

        ns.SUFFIX = "ACTPARENTS"
        for activity_name in activities_postfix_parents:
            ns.handle = name_to_email(activity_name)
            ns.full_email = ns('{handle}{SUFFIX}')
            with open(ns('{path}{SLASH}{base}{EXT}'), 'a') as f:
                f.write(ns('{full_email}{COLON}{SPACE}{INCLUDE}' + \
                           '{activities_path}{SLASH}{full_email}{EXT}{NEWLINE}'))
            with open(ns('{activities_path}{SLASH}{full_email}{EXT}'), 'a') as f:
                f.write("\n".join(activities_postfix_parents[activity_name]))

        # run newaliases command on exit if we're on the server
        newaliases_path = config_get_section_attribute('EMAIL', 'newaliases_path')
        if newaliases_path:
            self.logger.info("Running newaliases")
            p = subprocess.Popen(newaliases_path, shell=True)
            self.logger.info(p.communicate())
        else:
            self.logger.warn("newaliases not run!")
        #TODO: If received error, should email admin
