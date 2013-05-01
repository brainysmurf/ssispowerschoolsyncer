from Students import Students
from utils.Dates import get_years_since_enrolled

class Breakdown:
    """ Represents a unit """

    round_to = 1
    
    def __init__(self, identity):
        self.identity = identity
        self.number_koreans = 0
        self.number_chinese = 0
        self.number_other = 0
        self.percent_koreans = 0
        self.percent_chinese = 0
        self.percent_other = 0
        self._total = 0

    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, value):
        self._total = value
        self.percent_koreans = round((self.number_koreans / self._total) * 100, self.round_to)
        self.percent_chinese = round((self.number_chinese / self._total) * 100, self.round_to)
        self.percent_other = round((self.number_other / self._total) * 100, self.round_to)

    def add(self, student):
        if student.is_chinese:
            self.number_chinese += 1
        elif student.is_korean:
            self.number_koreans += 1
        else:
            self.number_other += 1
        self.total += 1

    def output(self):
        pass

import datetime

class GradeBreakdown(Breakdown):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.years_here = {}        
    
    def add(self, student):
        super().add(student)
        years = str(student.years_enrolled)[0]
        if not years in self.years_here.keys():
            self.years_here[years] = []
        self.years_here[years].append(student)

    def output(self):
        if not self.years_here:
            return
        for year in list(self.years_here.keys()):
            print("\t\t{} kids who have been for {} years".format(len(self.years_here), year))

class HRBreakdown(Breakdown):
    pass

class Breakdowns:
    """ Separates into units """

    def __init__(self):
        self._db = {}

    def add(self, student):
        target = '   all'
        secondary = '  secondary'
        elementary = '  elementary'
        target_grade = " grade_{grade}".format(**student.__dict__)
        target_hr    = "grade_{homeroom}".format(**student.__dict__)
        if not target in self._db.keys():
            self._db[target] = Breakdown('Overall')
        if not target_grade in self._db.keys():
            self._db[target_grade] = GradeBreakdown('Grade {}'.format(student.grade))
        if not target_hr in self._db.keys():
            self._db[target_hr] = HRBreakdown('Homeroom {}'.format(student.homeroom))
        if not secondary in self._db.keys():
            self._db[secondary] = Breakdown('Secondary')
        if not elementary in self._db.keys():
            self._db[elementary] = Breakdown('Elementary')

        self._db[target].add(student)
        if student.is_secondary:
            self._db[secondary].add(student)
            for course in student.courses():
                pass
                
        if student.is_elementary:
            self._db[elementary].add(student)
        self._db[target_grade].add(student)
        self._db[target_hr].add(student)

    def output(self):
        keys = list(self._db.keys())
        keys.sort()
        for key in keys:
            print("In {identity} there are:\n\t{number_koreans} koreans ({percent_koreans})\n\t{number_chinese} chinese ({percent_chinese})\n\t{number_other} other ({percent_other})\n\t---\n\t{_total} total".format(**self._db[key].__dict__))
            self._db[key].output()

if __name__ == "__main__":

    class Settings:
        def __init__(self):
            self.verbose = False
            self.courses = True
            self.teachers = True

    students = Students(Settings())
    breakdowns = Breakdowns()

    for student_key in students.get_student_keys():
        student = students.get_student(student_key)
        breakdowns.add(student)

    breakdowns.output()
