from psmdlsyncer.Students import Students, put_in_order

from psmdlsyncer.utils.Formatter import Smartformatter
from psmdlsyncer.utils.DB import DragonNetDBConnection


if __name__ == "__main__":

    students = Students()
    
    db = DragonNetDBConnection()
    results = db.get_all_users_activity_enrollments()
    results.sort(key=lambda x: x[0])  # sort by name
    old_name = ''
    sf = Smartformatter()
    sf.tab = '\t'
    sf.newline = '\n'

    expanded = []
    for result in results:
        sf.name, student_key = result
        student = students.get_student(student_key)
        if not student:
            continue
        sf.student = student.lastfirst
        if sf.name == old_name:
            print(sf('{tab}{student}'))
        else:
            print(sf('{newline}{name}'))
            old_name = sf.name
        expanded.append( (student.homeroom, student.lastfirst, sf.name) )

    expanded.sort(key=lambda x: put_in_order(x[0]))
    last_homeroom = ''
    last_lastfirst = ''
    for item in expanded:
        sf.homeroom, sf.lastfirst, sf.activity = item
        if sf.homeroom != last_homeroom:
            print(sf('\n{homeroom}'))
        if sf.lastfirst != last_lastfirst:
            print(sf('{lastfirst}'))
        print(sf('{tab}{activity}'))


        last_homeroom, last_lastfirst = sf.homeroom, sf.lastfirst
