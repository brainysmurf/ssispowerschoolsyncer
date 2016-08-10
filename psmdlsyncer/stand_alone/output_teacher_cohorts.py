from psmdlsyncer.sql import MoodleDBSession
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.sql import MoodleDBSession

from psmdlsyncer.models.datastores.moodle import MoodleTree

if __name__ == '__main__':
    moodle = MoodleTree()
    moodle.process()

    m = MoodleDBSession()
    mod = ModUserEnrollments()

    for idnumber,cohort in m.get_cohorts():
        if idnumber and cohort:
            if idnumber in moodle.teachers.get_keys():
                print(idnumber, cohort)

    from IPython import embed;embed()