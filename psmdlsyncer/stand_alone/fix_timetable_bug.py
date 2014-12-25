
from psmdlsyncer.models.datastores.autosend import AutoSendTree
from psmdlsyncer.models.datastores.moodle import MoodleTree
from psmdlsyncer.sql.MDB import MoodleDBSession
from psmdlsyncer.php import ModUserEnrollments

import re
from collections import defaultdict

if __name__ == "__main__":

    autosend = AutoSendTree()
    moodle = MoodleTree()
    moodle.process()
    autosend.process()
    dragonnet = MoodleDBSession()
    mod = ModUserEnrollments()
    results = dragonnet.get_timetable_data(active_only=False)
    TimetableInfo = dragonnet.table_string_to_class('ssis_timetable_info')

    # First thing we need to do is adjust the timetable info so that the comment
    # Has the section info
    reverse = {}
    for key, value in autosend.groups.section_maps.items():
        reverse[value] = key

    for item in results:
        # Find the section info by looking through step-by-step
        if item.name in reverse:
            section = reverse[item.name]
            with dragonnet.DBSession() as session:
                # Get the object in the db, change the comment
                db_obj = session.query(TimetableInfo).filter_by(id=item.id).one()
                db_obj.comment = section
        else:
            print('This group {} not found in autosend.groups.section_maps'.format(item.name))
            continue

    pattern = '-[a-z]+$'  # a hyphen followed by alphas at the end of the string, removes -a, -b, etc
    delete = ''           # used in re.sub to delete the above

    for user_idnumber in set([r.student_idnumber for r in results]):
        compilation = []
        already = []
        belong_to_this_user = [r for r in results if r.student_idnumber==user_idnumber]
        for this in belong_to_this_user:
            if not '{}-{}'.format(this.teacher_idnumber, this.course_idnumber) in already:
                already.append('{}-{}'.format(this.teacher_idnumber, this.course_idnumber))
                like_these = [l for l in belong_to_this_user if l.teacher_idnumber == this.teacher_idnumber and l.course_idnumber == this.course_idnumber]

                # If we have two groups with the same name (minus the -a, -b)...
                # ...and one of them is active but the other is inactive
                if len(like_these) == 2 and (like_these[0].active + like_these[1].active == 1):

                    # Reverse ourselves to the original
                    if like_these[0].active == 1:
                        active_one = like_these[0]
                        inactive_one = like_these[1]
                    else:
                        active_one = like_these[1]
                        inactive_one = like_these[0]

                    # Okay, now do the adjustments on the database.
                    # Adjust the timetable info table
                    with dragonnet.DBSession() as session:
                        inactive_db_one = session.query(TimetableInfo).filter_by(id=inactive_one.id).one()
                        active_db_one = session.query(TimetableInfo).filter_by(id=active_one.id).one()

                        # Filter by this because from above we know we have the right stuff
                        if inactive_db_one.comment == 'psmdlsyncer':
                            active_db_one.active = 0
                            inactive_db_one.active = 1
                            inactive_db_one.comment = active_one.comment
                            session.delete(active_db_one)  # this is now the inactive one...

                    # And remove them from the group
                    mod.remove_user_from_group(user_idnumber, active_one.name)
                    parent = user_idnumber[:-1] + 'P'
                    mod.remove_user_from_group(parent, active_one.name)


    # Let's look through the groups now

    # correct_dict = defaultdict(list)
    # other_dict = defaultdict(list)

    # for student_key in moodle.students.get_keys():
    #     student = moodle.students.get_key(student_key)

    #     user = dragonnet.get_user_from_idnumber(student.num)

    #     groups = [g.name for g in student.groups]

    #     for i1 in range(int(len(groups))):
    #         for i2 in range(i1, len(groups)):
    #             g1 = groups[i1]
    #             g2 = groups[i2]
    #             if not g1 == g2 and re.sub(pattern, delete, g1) == re.sub(pattern, delete, g2):
    #                 group_base = re.sub(pattern, delete, g1)

    #                 autosend_student = autosend.students.get_key(student.num)
    #                 found = False
    #                 for this_group in [g.name for g in autosend_student.groups]:
    #                     if this_group == g1:
    #                         correct_dict[student].append(this_group)
    #                         found = True
    #                     elif this_group == g2:
    #                         correct_dict[student].append(this_group)
    #                         found = True
    #                 if not found:
    #                     other_dict[student].append(group_base)

    # print(len(correct_dict.keys()))
    # for student in correct_dict.keys():
    #     print('{} ({}) in grade {} has {} groups ({})'.format(
    #         student.username,
    #         student.num,
    #         student.grade,
    #         len(correct_dict[student]),
    #         ' and '.join(correct_dict[student])
    #         ))
    # print('-----')
    # print(len(other_dict.keys()))
    # for student in other_dict.keys():
    #     print('{} ({}) in grade {} has {} groups ({})'.format(
    #         student.username,
    #         student.num,
    #         student.grade,
    #         len(other_dict[student]),
    #         ' and '.join(other_dict[student])
    #         ))

