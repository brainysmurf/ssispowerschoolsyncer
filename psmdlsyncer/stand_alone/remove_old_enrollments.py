
from psmdlsyncer.sql import MoodleDBSession
from psmdlsyncer.db import DBSession
from psmdlsyncer.db.MoodleDB import *
from sqlalchemy import and_, not_, or_
from sqlalchemy import desc, asc
#                         join(GroupsMember, GroupsMember.userid == User.id).\
#                        join(Group, and_(
#                            Group.id == GroupsMember.groupid,
#                            Group.courseid == Course.id
#                            )).\

class Better(MoodleDBSession):

    def unenrol_like_enrollments(self, like):
        with DBSession() as session:
            schedule = session.query(
                    Course.idnumber.label("courseID"), User.idnumber.label("userID"), User.username.label('username'), Role.shortname.label('rolename'), Group.name.label('group_name')).\
                    select_from(User).\
                        join(RoleAssignment, RoleAssignment.userid == User.id).\
                        join(Context, Context.id == RoleAssignment.contextid).\
                        join(Course, and_(Context.instanceid == Course.id, Context.contextlevel==50)).\
                        join(CourseCategory, CourseCategory.id == Course.category).\
                        join(Role, Role.id == RoleAssignment.roleid).\
                        outerjoin(GroupsMember, GroupsMember.userid == User.id).\
                        outerjoin(Group, and_(
                            Group.id == GroupsMember.groupid,
                            Group.courseid == Course.id
                            )).\
                        filter(
                            and_(
                                #CourseCategory.path == ('/{}'.format(self.TEACHING_LEARNING_CATEGORY_ID)),   # TODO: get roleid on __init__
                                CourseCategory.path.like('/{}/%'.format(self.TEACHING_LEARNING_CATEGORY_ID)),   # TODO: get roleid on __init__
                                Course.idnumber != '',
                                User.idnumber.like(like),
                            )).\
                        order_by(asc(Role.id))   # sort by role.id because it's in the natural order expected (teachers first, then students, then parents)
            for item in schedule.all():
                yield item

if __name__ == "__main__":
    from psmdlsyncer.php import ModUserEnrollments
    moodlemod = ModUserEnrollments()
    moodle = Better()
    already = []
    for item in moodle.unenrol_like_enrollments('%99P'):
        course_idnumber, user_idnumber, _email, _role, group_idnumber = item
        unique = user_idnumber+user_idnumber
        if group_idnumber is None and not unique in already:
            #moodlemod.deenrol_parent_from_course(user_idnumber, course_idnumber)
            already.append( unique )
            print(item)