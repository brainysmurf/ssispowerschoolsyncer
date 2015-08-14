from psmdlsyncer.models.base import BaseModel
from psmdlsyncer.utils import NS, weak_reference
from psmdlsyncer.utils.Counter import Counter

class Parent(BaseModel):
    """
    Hey, everything comes from the children
    except cohorts
    """
    kind = 'parent'

    def __init__(self, idnumber):
        """ SETS COMMON ATTRIBUTES, CALLS add_child """
        self.family_id = self.ID = self.idnumber = idnumber
        self._children = []
        self._cohorts = ['parentsALL']
        self._username = None
        self.custom_profile_isparent = True

    @property
    def grades(self):
        return [child.grade for child in self.children]

    @property
    def homerooms(self):
        result = []
        for child in self.children:
            result.append(child.homeroom)
        return result

    @property
    def emails(self):
        result = []
        for child in self.children:
            result.extend(child.guardian_emails)
        return set(result)

    @property
    def username(self):
        """
        Look at the common emails between all the children
        and pick the second one (assuming there are two)
        Reason for this is because there is no way for a computer to know
        which one is which
        """
        c = Counter()
        for child in self.children:
            for email in child.parent_emails:
                c.add(email)
        common = c.maximum_in_order_added
        # TODO: do a check here with common
        if len(common) == 1:
            return common[0]
        elif len(common) > 1:
            return common[1]
        else:
            return "<no username?>"

    @property
    def email(self):
        return self.username

    @property
    def courses(self):
        result = []
        for child in self.children:
            result.extend(child.courses)
        return set(result)

    def add_cohort(self, cohort):
        if not cohort in self._cohorts:
            self._cohorts.append(cohort)

    @property
    def enrollments(self):
        result = {}
        for child in self.children:
            result.update(child.enrollments)
        return result

    def get_enrollments(self):
        for course in self.enrollments:
            for group in self.enrollments[course]:
                yield course, group

    @property
    def groups(self):
        result = []
        for child in self.children:
            result.extend(child.groups)
        return set( result )

    @property
    def group_idnumbers(self):
        return set([group.ID for group in self.groups])

    @property
    def cohorts(self):
        ret = self._cohorts
        for child in self.children:
            grade = child.grade
            #substituted_grade = {-1: 'K', -2: ''}
            ret.append('parents{}'.format(grade))
        return ret

    @property
    def cohort_idnumbers(self):
        return set(self.cohorts)

    @property
    def teacher_idnumbers(self):
        return set([teacher.ID for teacher in self.teachers])

    @property
    def teachers(self):
        result = []
        for child in self.children:
            result.extend(child.teachers)
        return set(result)

    def add_child(self, child):
        """ SET ATTRIBUTES THAT DEPEND ON child HERE """
        if not child.ID in self.children_ids:
            self._children.append( weak_reference(child) )
            if child.is_secondary:
                self.add_cohort('parentsSEC')
            if child.is_elementary:
                self.add_cohort('parentsELEM')

    @property
    def children(self):
        return [child() for child in self._children]

    @property
    def children_ids(self):
        return [child.ID for child in self.children]

    @property
    def number_courses(self):
        return len(self.courses)

    @property
    def number_groups(self):
        return len(self.groups)

    def __sub__(self, other):

        for item in super().__sub__(other):
            yield item

        # Handle cohorts (site-wide groups)
        for to_add in set(other.cohort_idnumbers) - set(self.cohort_idnumbers):
            ns = NS()
            ns.status = 'add_to_cohort'
            ns.left = self
            ns.right = other
            ns.param = to_add
            yield ns

        for to_remove in set(self.cohort_idnumbers) - set(other.cohort_idnumbers):
            ns = NS()
            ns.status = 'remove_from_cohort'
            ns.left = self
            ns.right = other
            ns.param = to_remove
            yield ns

        # Other things
        attrs = []
        for attr in attrs:
            if not getattr(self, attr) == getattr(other, attr):
                ns = NS()
                ns.status = attr+'_changed'
                ns.left = self
                ns.right = other
                ns.param = getattr(other, attr)
                yield ns

        for course in set(other.enrollments.keys()) - set(self.enrollments.keys()):
            for group in other.enrollments[course]:
                ns = NS()
                ns.status = 'enrol_parent_into_course'
                ns.left = self
                ns.right = other
                to_add = NS()
                to_add.course = course
                to_add.group = group
                ns.param = to_add
                yield ns

        # Go through each course that they share, and check that
        # they have the same groups, if not, do what's right
        for course in set(self.enrollments.keys()) and set(other.enrollments.keys()):
            self_groups = self.enrollments.get(course, [])
            other_groups = other.enrollments.get(course, [])
            for group in other_groups:
                if not group in self_groups:
                    ns = NS()
                    ns.status = 'add_to_group'
                    ns.left = self
                    ns.right = other
                    to_add = NS()
                    to_add.course = course
                    to_add.group = group
                    ns.param = to_add
                    yield ns
            for group in self_groups:
                if not group in other_groups:
                    ns = NS()
                    ns.status = 'remove_from_group'
                    ns.left = self
                    ns.right = other
                    to_remove = NS()
                    to_remove.course = course
                    to_remove.group = group
                    ns.param = to_remove
                    yield ns

        for course in set(self.enrollments.keys()) - set(other.enrollments.keys()):
            for group in self.enrollments[course]:
                ns = NS()
                ns.status = 'deenrol_parent_from_course'
                ns.left = self
                ns.right = other
                to_remove = NS()
                to_remove.course = course
                to_remove.group = group
                ns.param = to_remove
                yield ns

    def __repr__(self):
        ns = NS()
        ns.homerooms = " ".join(self.homerooms)
        ns.emails = ", ".join(self.emails)
        ns.parents_of = "Parents of " + ", ".join(self.children_ids)
        ns.family_id = self.family_id
        ns.ID = self.ID
        ns.homerooms = "(" + ", ".join(self.homerooms) + ")"
        ns.courses = "{} courses".format(len(self.courses))
        ns.groups = "{} groups".format(len(self.groups))
        return ns("<Parent {ID}: {parents_of} {homerooms}>")

class MoodleParent(Parent):

    def __init__(self, idnumber, database_id="", dunno="", username=""):
        super().__init__(idnumber)
        self.idnumber = idnumber
        self._username = username
        self.database_id = database_id
        self._enrollments = {}

    @property
    def username(self):
        return self._username

    @property
    def enrollments(self):
        """
        Overrides to just return what's inside me, instead of the Parent class' behavior
        which is to return the union of childrens' enrollments
        """
        return self._enrollments

    def add_enrollment(self, enrollment):
        # Method that allows a controller to manually put in the enrollments
        # needed since default behavior is to take on enrollments from child
        # what is wrong for moodle, should come from the database
        not_in_self = enrollment.keys() - self._enrollments.keys()
        already_in_self = [key for key in enrollment.keys() if not key in not_in_self]

        # First just do a simple update with keys that we don't have yet
        for key in not_in_self:
            self.enrollments[key] = enrollment[key]

        for key in already_in_self:
            for item in enrollment[key]:
                if not item in self.enrollments[key]:
                    self.enrollments[key].append(item)

    def __repr__(self):
        ns = NS()
        ns.emails = ", ".join(self.emails)
        ns.parents_of = "Parents of " + ", ".join(self.children_ids)
        ns.homerooms = "(" + ", ".join(self.homerooms) + ")"
        ns.family_id = self.family_id
        ns.ID = self.ID
        return ns("<MoodleParent {ID}: {parents_of} {homerooms}>")


