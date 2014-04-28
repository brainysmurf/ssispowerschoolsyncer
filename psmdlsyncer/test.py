from psmdlsyncer.sql.MoodleDBConnection import MoodleDBConnection2 as m
from psmdlsyncer.sql.MoodleDB import Group, GroupsMember
from sqlalchemy.sql import select

moodle = m()

query = select(Group, GroupsMember).filter(Group.id == GroupsMember.groupid)

from IPython import embed
embed()




