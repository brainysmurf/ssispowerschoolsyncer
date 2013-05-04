from Students import Students
from utils.Dates import get_years_since_enrolled

class Breakdown:
    """ Represents a unit """

    round_to = 1
    exclusions = ['is_student', 'is_elementary', 'is_secondary']
    
    def __init__(self, identity):
        self.identity = identity
        self._total = 0

    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, value):
        """
        Recalculate percentages every time total has been counted
        """
        self._total = value
        for nationality in self.nationalities():
            number_key, percent_key = self.nationality_keys(nationality)
            number, percent = self.nationality_info(nationality)
            setattr(self, percent_key, round((number / self._total) * 100, self.round_to))
        for group in self.groups():
            number_key, percent_key = self.group_keys(group)
            number, percent = self.group_info(group)
            setattr(self, percent_key, round((number / self._total) * 100, self.round_to))

    def add(self, student):
        nationality_number_key, nationality_percent_key = self.nationality_keys(student.nationality)
        for key in student.__dict__.keys():
            if key.startswith('is_') and getattr(student, key) and not key in self.exclusions:
                group_name = key.replace('is_', '')
                group_number_key, group_percent_key = self.group_keys(group_name)
                if not hasattr(self, group_number_key):
                    setattr(self, group_number_key, 0)
                if not hasattr(self, group_percent_key):
                    setattr(self, group_percent_key, 0)
                group_number, group_percent = self.group_info(group_name)
                setattr(self, group_number_key, group_number + 1)

        # set default values:
        if not hasattr(self, nationality_number_key):
            setattr(self, nationality_number_key, 0)
        if not hasattr(self, nationality_percent_key):
            setattr(self, nationality_percent_key, 0)
        setattr(self, nationality_number_key, getattr(self, nationality_number_key) + 1)
        # percentages are calculated on below call
        self.total += 1

    def groups(self):
        for attr in self.__dict__.keys():
            if attr.startswith('group_number_'):
                yield attr.replace('group_number_', '')

    def group_keys(self, group):
        return ('group_number_{}'.format(group), 'group_percent_{}'.format(group))

    def group_info(self, group):
        number, percent = self.group_keys(group)
        return (getattr(self, number), getattr(self, percent))

    def nationalities(self):
        for attr in self.__dict__.keys():
            if attr.startswith('number_'):
                yield attr.replace("number_", '')

    def nationality_keys(self, nationality):
        return ('number_{}'.format(nationality.lower()), 'percent_{}'.format(nationality.lower()))

    def nationality_info(self, nationality):
        number_key, percent_key = self.nationality_keys(nationality)
        return (getattr(self, number_key), getattr(self, percent_key))

    def output(self):
        print("In {identity} there are:".format(identity=self.identity))
        groups = list(self.groups())
        groups.sort()
        #print('\tBy groups')
        for group in groups:
            number, percent = self.group_info(group)
            d = dict(group=group.upper(), number=number, percent=percent)
            print("\t{group}: {number} ({percent}%)".format(**d))
        nationalities = list(self.nationalities())
        nationalities.sort()
        #print('\tBy passports')
        for nationality in nationalities:
            number, percent = self.nationality_info(nationality)
            d = dict(nationality=nationality.title(), number=number, percent=percent)
            print("\t{nationality}: {number} ({percent}%)".format(**d))
        total_nationalities = len(list(self.nationalities()))
        total_groups = len(list(self.groups()))
        print("\t---\n\t{total} total individuals with passports from {total_nationalities} countries and {total_groups} group(s)".format(total=self.total,
                                                                                                                                 total_nationalities=total_nationalities,
                                                                                                                                 total_groups=total_groups))

class GradeBreakdown(Breakdown):
    def add(self, student):
        super().add(student)

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
