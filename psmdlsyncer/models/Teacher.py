"""
"""
from psmdlsyncer.models.Entry import Entry
import re
from psmdlsyncer.utils.Utilities import no_whitespace_all_lower, derive_departments
PRIMARYSCHOOLID = 111
SECONDARYSCHOOLID = 112
class Teacher(Entry):
   def __init__(self, num, lastfirst, email, title, schoolid, status, **kwargs):
       self.num = num
       self.ID = num
       self.powerschool_id = num
       self.idnumber = self.num
       self.family_id = self.ID[:4] + 'P'
       self.kind = 'teacher'
       self.lastfirst = lastfirst
       self.email = email if email.strip() else None
       self.last, self.first = self.lastfirst.split(',')
       self.first = self.first.strip()
       self.last = self.last.strip()
       if not self.email:
           self.email = "{}@ssis-suzhou.net".format(re.sub(r'[^a-z]', '', "{}{}".format(self.first, self.last).lower()))
       self.preferred_name = self.first + " " + self.last
       self.profile_bool_details = title
       if email:
           self.username = no_whitespace_all_lower(self.email.split('@')[0])
       else:
           self.username = no_whitespace_all_lower(self.preferred_name)
       self.title = title
       self._courses = []
       self._students = []
       self._teachers = []
       self._groups = []
       self._parents = []
       self._departments = []
       self.is_primary = False
       self.is_secondary = False
       self.homeroom = None
       if schoolid == str(PRIMARYSCHOOLID):
           self.is_primary = True
           self.profile_bool_iselemteacher = True
       if schoolid == str(SECONDARYSCHOOLID):
           self.is_secondary = True
           self.profile_bool_issecteacher = True
       self.profile_extra_isteacher = True
   def add_course(self, course):
      """ UPDATES INTERNAL AS WELL AS DETECTS HOMEROOM """
      course_id = course.ID
      if course_id not in self._courses:
         if course_id.startswith('HROOM'):
            self.homeroom = int(re.sub('[A-Z]', '', course_id.upper()))
         self._courses.append(course_id)
   def add_student(self, student):
      if not student:
         return
      if student.ID not in self._students:
         self._students.append(student.ID)
   def add_group(self, group):
       if group.ID not in self._groups:
           self._groups.append(group.ID)
   def add_teacher(self, teacher):
      if teacher.ID not in self._teachers:
         self._teachers.append(teacher.ID)
   def add_parent(self, parent):
      if not parent:
         return
      if parent.ID not in self._parents:
         self._parents.append(parent.ID)
   @property
   def students(self):
       return self._students
   @property
   def courses(self):
       return self._courses
   @property
   def parents(self):
       return self._parents
   @property
   def groups(self):
       return self._groups
   def derive_cohorts(self):
       """ Returns cohorts, dynamically created """
       l = self.get_departments()
       if self.is_secondary:
           l.append('teachersSEC')
       if self.is_primary:
           l.append('teachersELEM')
       if self.is_secondary or self.is_primary:
           l.append('teachersALL')
       return l
   def get_departments(self):
       self._departments = derive_departments([c for c in self.courses()])
       return self._departments
   def __repr__(self):
       return self.format_string("{first}{preferred_name}:{username}{mid}{courses_str}", first="+ ", mid="\n| ", last="| ", courses_str=", ".join([a for a in self._courses if a]))

if __name__ == "__main__":
   pass
