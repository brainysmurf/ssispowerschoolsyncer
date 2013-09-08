from psmdlsyncer.Students import Students, put_in_order

from psmdlsyncer.utils.Formatter import Smartformatter
from psmdlsyncer.utils.DB import DragonNetDBConnection
from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.utils.FilesFolders import clear_folder

import re

def name_to_email(long_name):

    try:
        where = long_name.index(')')
    except ValueError:
        where = -1
    where += 1
    long_name = long_name[where:].strip().lower()
    return re.sub('[^a-z]', '', long_name)
    

if __name__ == "__main__":

    students = Students()
    
    db = DragonNetDBConnection()
    sf = Smartformatter()

    results = db.get_all_users_activity_enrollments()
    sf.domain = 'student.ssis-suzhou.net'
    sf.AT = '@'

    from collections import defaultdict
    postfix = defaultdict(list)
    homerooms = defaultdict( lambda : defaultdict(list) )

    # PARSE RESULTS
    for result in results:
        activity_name, student_key = result
        student = students.get_student(student_key)
        if not student:
            continue
        homerooms[student.homeroom][student.num].append(activity_name)
        postfix[activity_name].append(student.email)

    homerooms_sorted = list(homerooms.keys())
    homerooms_sorted.sort(key=put_in_order)
    for homeroom in homerooms_sorted:
        print(homeroom)
        for student_key in homerooms[homeroom]:
            student = students.get_student(student_key)
            activities = ", ".join( homerooms[homeroom][student_key] )
            print('\t' + student.lastfirst + ': ' + activities)

    # DO THE ACTIVITY EMAILS
    sf.path = config_get_section_attribute('DIRECTORIES', 'path_to_postfix')
    sf.base = 'activities'
    sf.SUFFIX = "ACT"
    sf.EXT = '.txt'
    sf.INCLUDE = ':include:'
    sf.activities_path = sf('{path}{SLASH}{base}')
    sf.space = ' '
    clear_folder(sf.activities_path)
    with open(sf('{path}{SLASH}{base}{EXT}'), 'w'):
        pass

    for activity_name in postfix:
        sf.handle = name_to_email(activity_name)
        sf.full_email = sf('{handle}{SUFFIX}')
        with open(sf('{path}{SLASH}{base}{EXT}'), 'a') as f:
            f.write(sf('{full_email}{COLON}{SPACE}{INCLUDE}{activities_path}{SLASH}{full_email}{EXT}{NEWLINE}'))
        with open(sf('{activities_path}{SLASH}{full_email}{EXT}'), 'a') as f:
            f.write("\n".join(postfix[activity_name]))

    output = []
    for activity_name in postfix:
        output.append(name_to_email(activity_name))

    output.sort()
    for activity in output:
        sf.activity = activity
        sf.email = sf('{activity}{SUFFIX}{AT}{domain}')
        print(sf( '<a href="mailto:{email}">{email}</a><br />' ))
