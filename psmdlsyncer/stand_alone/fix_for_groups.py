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

    for student in moodle.students.get_objects():
        other = autosend.students.get_key(student.idnumber)
        if not other:
            continue
        counter = defaultdict(list)
        for group in student.groups:
            if '-' in group.group_id:
                g, s = group.group_id.split('-')
                counter[g].append(group)

        for group_name in counter:
            if len(counter[group_name]) == 2:

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
                    winner = second_group if group1time < group2time else first_group

                    print('Removing {} from {}'.format(student, winner))
                    php.remove_user_from_group(student.idnumber, winner.group_id)

            elif len(counter[group_name]) > 2:
                print("more than 2:")
                print(counter[group_name])
                input('------------')