import re
from psmdlsyncer.utils.Dates import get_year_of_graduation
from psmdlsyncer.utils.Utilities import derive_depart, department_heads
from psmdlsyncer.utils import weak_reference
from psmdlsyncer.models.base import BaseModel
from psmdlsyncer.utils.Utilities import convert_short_long
from psmdlsyncer.utils import NS

class Course(BaseModel):
    kind = "course"
    grade_sep = ','

    def __init__(self, course_id, course_name, grade="", database_id=0):
        """
        @param grade has to be a string by default
        @param database_id has to be an integer
        """
        self.ID, self.name = course_id, course_name
        if 'HROOM' in self.ID:
            self.is_homeroom = True
        else:
            self.is_homeroom = False
        self.course_id = self.idnumber = self.ID
        self.department = derive_depart(self.name)
        self.heads = department_heads.get(self.department)
        self.grade = grade
        self.database_id = database_id
        if self.grade_sep in grade:
            self.grade = sorted(grade.split(self.grade_sep))
        elif self.grade is "":
            # determine it as best we can...
            # which in this case is looking for stuff inside the parenths
            # at the end of the string, taking into account possible whitespace
            match = re.search('\((.+)\)\W?$', self.name)
            if not match:
                self.grade = "-100"  # dunno what to put here really
            else:
                self.grade = match.group(1).replace('/', ',')
            if self.grade_sep in self.grade:
                self.grade = sorted(self.grade.split(self.grade_sep))
            else:
                self.grade = [self.grade]
        if not self.heads:
            pass
        self.exclude = False
        self._teachers = []
        self._students = []
        self._groups = []
        self._parents = []

    def convert_grade(self):
        return self.grade_sep.join(sorted(self.grade))

    def add_teacher(self, teacher):
        if not teacher:
            return
        reference = weak_reference(teacher)
        if not reference in self._teachers:
            self._teachers.append( reference )

    def add_student(self, student):
        reference = weak_reference(student)
        if not reference in self._students:
            self._students.append( reference )

    def add_parent(self, parent):
        reference = weak_reference(parent)
        if not reference not in self._parents:
            self._parents.append( reference )

    def add_group(self, group):
        reference = weak_reference(group)
        if not reference in self._groups:
            self._groups.append( reference )

    def associate(self, group, teacher, student):
        self.add_group(group)
        self.add_teacher(teacher)
        self.add_student(student)

    @property
    def teachers(self):
        return [teacher() for teacher in self._teachers if teacher]

    @property
    def students(self):
        return [student() for student in self._students]

    @property
    def groups(self):
        return [group() for group in self._groups]

    @property
    def parents(self):
        return self._parents

    def __sub__(self, other):
        if self.grade != other.grade:
            ns = NS()
            ns.status = 'course_grade_changed'
            ns.left = self
            ns.right = other
            ns.param = other.grade
            yield ns

    def __repr__(self):
        return self.format_string("<Course: {ID} ({name})>") #" : {teachers}", first="(", mid="| ", last=") ", teachers=teacher_txt)
