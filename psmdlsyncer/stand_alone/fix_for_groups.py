from psmdlsyncer.settings import config, config_get_section_attribute

from psmdlsyncer.models.datastores.moodle import MoodleTree
from psmdlsyncer.models.datastores.autosend import AutoSendTree
from collections import defaultdict
from psmdlsyncer.php import CallPHP
from psmdlsyncer.db.MoodleDB import GroupsMember as Member
import datetime

from psmdlsyncer.db import DBSession
from psmdlsyncer.sql import MoodleDBSession
from sqlalchemy import and_

test = False
really = not test

if __name__ == "__main__":

    moodle = MoodleTree()
    autosend = AutoSendTree()
    moodle.process()
    autosend.process()

    sql = MoodleDBSession()
    db = MoodleDBSession()

    Group = db.table_string_to_class('groups')
    User = db.table_string_to_class('user')
    Enrol = db.table_string_to_class('user_enrolments')
    php = CallPHP()

    renames = defaultdict(list)

    for student in moodle.students.get_objects():
        other = autosend.students.get_key(student.idnumber)
        if not other:
            continue
        counter = defaultdict(list)
        not_in_autosend = []
        for group in student.groups:
            if '-' in group.group_id:
                g, s = group.group_id.split('-')

                if autosend.groups.get_key(group.group_id):
                    counter[g].append(group)
                else:
                    not_in_autosend.append(group.group_id)

        for group_name in counter:
            if len(counter[group_name]) == 1:
                group = counter[group_name][0]
                base = group.idnumber.split('-')[0]

                as_group = autosend.groups.get_key(group.group_id)
                sec = as_group.section.split('-')[1]
                section_name = "{0} [{1}]".format(group.idnumber, sec)
                section_idnumber = "{0}-{1}".format(base ,sec)
                renames[group.idnumber].append("|".join([section_idnumber, section_name]))

            elif len(counter[group_name]) == 2:
                with DBSession() as session:
                    first_group = counter[group_name][0]
                    second_group = counter[group_name][1]

                    user = session.query(User).filter(User.idnumber == student.idnumber).one()

                    groupdb = session.query(Group).filter(Group.idnumber == first_group.group_id).one()

                    this_group = session.query(Member).\
                        filter(and_(Member.userid==user.id, Member.groupid==groupdb.id)).\
                        one()

                    group1time = datetime.datetime.fromtimestamp(this_group.timeadded)
                    groupdb = session.query(Group).filter(Group.idnumber == second_group.group_id).one()
                    this_group = session.query(Member).\
                        filter(and_(Member.userid==user.id, Member.groupid==groupdb.id)).\
                        one()

                    group2time = datetime.datetime.fromtimestamp(this_group.timeadded)

                    # Find the one to remove from
                    newest = second_group if group1time < group2time else first_group
                    orig = second_group if group1time > group2time else first_group

                    #print('Should remove {} from {}'.format(student, newest))

                    base = orig.idnumber.split('-')[0]

                    # Check to see if there is a section with the student hr equiv
                    as_group = autosend.groups.get_key(orig.group_id)
                    other_as_group = autosend.groups.get_key(newest.group_id)
                    if other_as_group.section.endswith(student.hr_letter):
                        as_group = other_as_group

                    sec = as_group.section.split('-')[1]
                    section_name = "{0} [{1}]".format(orig.idnumber, sec)
                    section_idnumber = "{0}-{1}".format(base, sec)
                    renames[orig.idnumber].append("|".join([section_idnumber, section_name]))

                    if really: php.remove_user_from_group(student.idnumber, newest.group_id)
                    if really: php.remove_user_from_group(student.family_id, newest.group_id)

            elif len(counter[group_name]) > 2:
                print("dude has more than 2: {}".format(counter[group_name]))

        for group in not_in_autosend:
            if really: php.remove_user_from_group(student.idnumber, group)
            if really: php.remove_user_from_group(student.family_id, group)

    for orig_idnumber in renames:
        sections = renames[orig_idnumber]
        if len(set(sections)) > 1:
            ssss = {}
            for ss in sections:
                s = ss.split('|')[0]
                ssss[s] = len([n for n in sections if n.split('|')[0] == s])
            items = ssss.items()
            winner = max(*items)[0]
        else:
            winner = sections[0].split('|')[0]

        with DBSession() as session:
            groupdb = session.query(Group).filter(Group.idnumber == orig_idnumber).one()
            _, name = sections[0].split('|')
            if really: groupdb.idnumber = winner
            if not groupdb.name or groupdb.name == orig_idnumber:
                if really: groupdb.name = name
            print("{} -> {}".format(orig_idnumber, winner))


