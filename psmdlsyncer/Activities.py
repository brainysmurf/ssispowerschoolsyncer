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
    results = db.get_all_users_activity_enrollments()
    results.sort(key=lambda x: x[0])  # sort by name
    old_name = ''
    sf = Smartformatter()
    sf.tab = '\t'
    sf.newline = '\n'

    # PARSE RESULTS
    from collections import defaultdict
    postfix = defaultdict(list)
    printout = []    
    
    for result in results:
        sf.name, student_key = result
        student = students.get_student(student_key)
        if not student:
            continue
        sf.student = student.lastfirst

        # printout
        if sf.name == old_name:
            print(sf('{tab}{student}'))
        else:
            print(sf('{newline}{name}'))
            old_name = sf.name

        printout.append( (student.homeroom, student.lastfirst, sf.name) )
        postfix[sf.name].append(student.email)

    # OUTPUT THE RESULTS IN HUMAN-READABLE FORM
    printout.sort(key=lambda x: put_in_order(x[0]))
    last_homeroom = ''
    last_lastfirst = ''
    for item in printout:
        sf.homeroom, sf.lastfirst, sf.activity = item
        if sf.homeroom != last_homeroom:
            print(sf('\n{homeroom}'))
        if sf.lastfirst != last_lastfirst:
            print(sf('{lastfirst}'))
        print(sf('{tab}{activity}'))

        last_homeroom, last_lastfirst = sf.homeroom, sf.lastfirst

    # DO THE ACTIVITY EMAILS
    sf.path = config_get_section_attribute('DIRECTORIES', 'path_to_postfix')
    sf.base = 'activities'
    sf.SUFFIX = "ACT"
    sf.SPACE = ' '
    sf.EXT = '.txt'
    sf.NEWLINE = '\n'
    sf.SLASH = '/'  # uppercase for readability
    sf.INCLUDE = ':include:'
    sf.activities_path = sf('{path}{SLASH}{base}')
    sf.space = ' '
    clear_folder(sf.activities_path)
    for activity_name in postfix:
        sf.handle = name_to_email(activity_name)
        sf.full_email = sf('{handle}{SUFFIX}')
        with open(sf('{path}{SLASH}{base}{EXT}'), 'a') as f:
            f.write(sf('{full_email}{SPACE}{INCLUDE}{activities_path}{SLASH}{full_email}{EXT}{NEWLINE}'))
        with open(sf('{activities_path}{SLASH}{full_email}{EXT}'), 'a') as f:
            f.write("\n".join(postfix[activity_name]))
