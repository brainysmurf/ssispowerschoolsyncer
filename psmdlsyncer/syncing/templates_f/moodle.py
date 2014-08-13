from .default import DefaultTemplate

class MoodleTemplate(DefaultTemplate):
    """
    Unpacks the info that comes in and sends it on to the PHP routines that acutally
    does the work
    Note: If you want to have some sort of queuing feature that, say, makes sure that
    "new_group" gets called before "add_to_group" (to ensure it's already there when adding it)
    This is the place to do it.
    """
    def __init__(self):
        super().__init__()
        self.moodle = MoodleDBSession()
        self.moodlemod = ModUserEnrollments()

        # Set up some things
        self.courses = []
        for course in self.moodle.get_teaching_learning_courses():
            self.courses.append(course.idnumber)
        self.groups = self.moodle.get_list_of_attributes('group', 'name')

    def course_exists(self, course_idnumber):
        return course_idnumber in self.courses

    def new_cohort(self, item):
        super().new_cohort(item)
        cohort_idnumber = item.param
        cohort_name = cohort_idnumber
        self.moodle.add_cohort(cohort_idnumber, cohort_name)

    def old_cohort(self, item):
        super().old_cohort(item)
        # Remove it?

    def new_student(self, item):
        """
        """
        if self.moodle.wrap_no_result(self.moodle.get_user_from_idnumber, item.right.idnumber):
            self.logger.warning("Student already exists, maybe they are not in the studentsALL group?.")
        else:
            super().new_student(item)
            student = item.right
            self.moodlemod.new_student(student)

    # def new_teacher(self, item):
    #     """
    #     """
    #     if self.moodle.wrap_no_result(self.moodle.get_user_from_idnumber, item.right.idnumber):
    #         self.logger.warning("Staff member {} already exists, not creating.".format(item.right))
    #     else:
    #         super().new_teacher(item)
    #         teacher = item.right
    #         self.moodlemod.new_teacher(teacher)

    def new_parent(self, item):
        """
        """
        super().new_parent(item)
        parent = item.right
        self.moodlemod.new_parent(parent)
        self.moodlemod.add_user_to_cohort(parent.idnumber, 'parentsALL')

    def new_group(self, item):
        """
        Although we detect new groups, the right thing to do is actually to create the group,
        as they are needed,
        when enrolling users.

        That's because groups and courses are inexplicably linked together
        and we have to do the checks for groups when enrolling anyway
        so best is to do the creation there
        """
        super().new_group(item)  # output

    # def new_course(self, item):
    #     super().new_course(item)
    #     course = item.right
    #     self.moodlemod.create_new_course(course.idnumber, course.name)

    def enrol_in_course(self, item):
        course_idnumber = item.param.course
        yes_no = course_idnumber in self.courses
        if yes_no:
            super().enrol_in_course(item)  # for output
        return yes_no

    def enrol_student_into_course(self, item):
        student = item.right.idnumber
        course = item.param.course
        group = item.param.group
        if self.enrol_in_course(item):   # for output and checking
            self.moodlemod.enrol_student_into_course(student, course, group) # just pass the whole schedule object itself
        else:
            self.default_logger("Did NOT enrol {} into course {}, because it does not exist in Moodle".format(item.right, course))

    def enrol_teacher_into_course(self, item):
        teacher = item.right.idnumber
        course = item.param.course
        group = item.param.group
        if self.enrol_in_course(item):   # for output and checking
            self.moodlemod.enrol_teacher_into_course(teacher, course, group) # just pass the whole schedule object itself
        else:
            self.default_logger("Did NOT enrol {} into course {}, because it does not exist in Moodle".format(item.right, course))

    def enrol_parent_into_course(self, item):
        parent = item.right.idnumber
        course = item.param.course
        group = item.param.group
        if self.enrol_in_course(item):   # for output and checking
            self.moodlemod.enrol_parent_into_course(parent, course, group) # just pass the whole schedule object itself
        else:
            self.default_logger("Did NOT enrol {} into course {}, because it does not exist in Moodle".format(item.right, course))

    def deenrol_teacher_from_course(self, item):
        pass
        # super().deenrol_from_course(item)   # for output
        # user = item.right.idnumber
        # course = item.param.course
        # group = item.param.group
        # self.moodlemod.deenrol_teacher_from_course(user, course)

    def deenrol_student_from_course(self, item):
        pass
        # super().deenrol_from_course(item)   # for output
        # user = item.right.idnumber
        # course = item.param.course
        # group = item.param.group
        # self.moodlemod.deenrol_student_from_course(user, course)

    def deenrol_teacher_from_course(self, item):
        pass
        # super().deenrol_from_course(item)   # for output
        # user = item.right.idnumber
        # course = item.param.course
        # group = item.param.group
        # self.moodlemod.deenrol_teacher_from_course(user, course)

    def deenrol_parent_from_course(self, item):
        pass
        # super().deenrol_from_course(item)   # for output
        # user = item.right.idnumber
        # course = item.param.course
        # group = item.param.group
        # self.moodlemod.deenrol_parent_from_course(user, course)

    def add_to_cohort(self, item):
        super().add_to_cohort(item)
        user = item.right.idnumber
        cohort = item.param
        self.moodlemod.add_user_to_cohort(user, cohort)

    def remove_from_cohort(self, item):
        pass
        # super().remove_from_cohort(item)
        # user = item.left.idnumber
        # cohort = item.param
        # self.moodlemod.remove_user_from_cohort(user, cohort)

    def new_group(self, item):
        course = item.right.course.ID
        group = item.param
        if group in self.groups:
            self.default_logger("Did NOT add group {} because it's already there....".format(group, course))
        elif course in self.courses:
            super().new_group(item)
            self.moodlemod.add_group(group, course)
        else:
            self.default_logger("Did NOT add group {} because course {} does not exist.".format(group, course))

    def new_custom_profile_field(self, item):
        """
        """
        right = item.right
        name = right.idnumber
        self.default_logger("Found a new custom profile field {}".format(name))
        self.moodle.make_new_custom_profile_field(name)

    def old_custom_profile_field(self, item):
        """
        This actually means that a particular user has lost a particular profile field
        (It does NOT mean that this profile field should be deleted...)
        or does it?
        """
        # not sure what to do yet

    def old_group(self, item):
        group = item.left
        course_idnumber = group.course_idnumber
        if course_idnumber not in self.courses:
            self.default_logger("Did NOT delete group {} because the correspoding course {} does not exist.".format(group, course_idnumber))
        else:
            super().old_group(item)
            self.moodlemod.delete_group(group.idnumber, course_idnumber)

    def add_to_group(self, item):
        user = item.right.idnumber
        group = item.param.group
        course = item.param.course
        if course in self.courses:
            super().add_to_group(item)
            # We don't actually need the course...

            self.moodlemod.add_user_to_group(user, group)
            #self.default_logger("Successfully put user {} into group {}".format(user, group))
        else:
            self.default_logger("Did NOT put {} in group {} because course {} does not exist.".format(user, group, course))

    def remove_from_group(self, item):
        super().remove_from_group(item)
        user = item.right.idnumber
        group = item.param.group
        course = item.param.course
        # We don't actually need the course...
        self.moodlemod.remove_user_from_group(user, group)

    def username_changed(self, item):
        user = item.left
        idnumber = user.idnumber
        from_what = item.left.username
        to_what = item.right.username
        if hasattr(user, 'login_method') and user.login_method == 'nologin':
            # Just go ahead and change it automatically, no need to inform anyone or anything
            # because the account isn't active anyway
            self.moodle.update_table('user', where={
                'idnumber':idnumber
                },
                username=to_what)
            super().username_changed(item)
        else:
            msg = "Student {} needs his/her username changed manually".format(from_what, to_what)
            if '_' in from_what:
                if from_what.replace('_', '') == to_what:
                    self.default_logger("Student {} with an underscore and whose username has NOT changed to {}.".format(from_what, to_what))
                else:
                    self.logger.warning(msg)
            else:
                self.logger.warning(msg)

    def custom_profile_value_changed(self, item):
        person = item.left.useridnumber
        field = item.param.field
        value = item.param.value
        self.moodle.set_user_custom_profile(person, field, value)

    def add_custom_profile_field_to_user(self, item):
        super().add_custom_profile_field_to_user(item)
        person = item.right.idnumber
        field = item.param.field
        value = item.param.value
        self.moodle.add_user_custom_profile(person, field, value)

    def homeroom_changed(self, item):
        super().homeroom_changed(item)
        student = item.left
        from_what = item.left.homeroom
        homeroom = item.param
        self.moodle.update_table('user', where={
            'idnumber':student.idnumber
            },
            department=homeroom)
        #self.default_logger("Successfully changed user {}'s homeroom from {} to {}".format(
        #    idnumber, from_what, to_what
        #    ))

    def course_grade_changed(self, item):
        for i in range(len(item.param)):
            grade = item.param[i]
            field = 'grade{}'.format(i+1)

            exists = self.moodle.get_rows_in_table('course_ssis_metadata',
                courseid = item.left.database_id,
                field=field)

            if not exists:
                self.moodle.insert_table('course_ssis_metadata',
                    courseid = item.left.database_id,
                    field=field,
                    value=grade)
            else:
                # we just need to update the existing one
                self.moodle.update_table('course_ssis_metadata',
                    where = dict(
                        courseid=item.left.database_id,
                        field=field,
                        ),
                    value=grade
                )

    def new_parent_link(self, item):
        """
        Go through all the children and make the association
        """
        super().new_parent_link(item)
        for child_idnumber in item.right.children:
            self.moodlemod.associate_child_to_parent(item.right.parent_idnumber, child_idnumber)

    def deassociate_child_from_parent(self, item):
        super().deassociate_child_from_parent(item)

    def new_mrbs_editor(self, item):
        super().new_mrbs_editor(item)
        self.moodle.add_mrbs_editor(item.param)

    def new_timetable(self, item):
        pass  # meaningless

    def old_timetable(self, item):
        pass # meaningless

    def new_timetable_data(self, item):
        super().new_timetable_data(item)
        self.moodle.add_timetable_data(item.right)

    def old_timetable_data(self, item):
        super().old_timetable_data(item)
        self.moodle.set_timetable_data_inactive(item.left)

    def new_course_metadata(self, item):
        super().new_course_metadata(item)
        self.moodle.add_course_metadata(item.right)

    def new_online_portfolio(self, item):
        super().new_online_portfolio(item)
        self.moodlemod.create_online_portfolio(item.param)
