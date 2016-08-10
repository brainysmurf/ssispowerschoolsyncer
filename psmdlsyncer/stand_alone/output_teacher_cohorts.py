from psmdlsyncer.sql import MoodleDBSession
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.sql import MoodleDBSession

from psmdlsyncer.models.datastores.moodle import MoodleTree

if __name__ == '__main__':
    moodle = MoodleTree()
    moodle.process()

    m = MoodleDBSession()
    mod = ModUserEnrollments()

    for idnumber, username, cohort in m.get_cohorts_with_username():
        if cohort:
            if moodle.teachers.get_from_attribute('username', username):
                print(idnumber, username, cohort)

    from IPython import embed;embed()