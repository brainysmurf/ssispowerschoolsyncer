from Students import Students
from utils.Dates import get_years_since_enrolled

class Breakdown:
    """ Represents a unit """

    round_to = 1
    exclusions = ['is_student', 'is_elementary', 'is_secondary']
    
    def __init__(self, identity):
        self.identity = identity
        self._total = 0
        self.years_enrolled = YearsEnrolled()

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
        self.years_enrolled.add(student)
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
        self.years_enrolled.output(self.total)

import datetime

class GradeBreakdown(Breakdown):
    pass

class YearsDatabase:
    round_to = 1
    
    def __init__(self, years):
        self.years = years
        self.duration_info = []
        self.nationality_info = {}

    def all_years(self):
        years = self.duration_info.keys()
        years.sort(reverse=True)
        return years

    def how_many_duration(self):
        return len(self.duration_info)

    def how_many_nationality(self, nationality):
        return len(self.nationality_info[nationality])

    def nationalities(self):
        result = []
        percents = []
        percent_dict = {}
        for key in list(self.nationality_info.keys()):
            how_many = self.how_many_nationality(key)
            p = round((how_many / how_many) * 100, self.round_to)
            percents.append(p)
            percent_dict[p] = self.nationality_info[key]

        percents.sort(reverse=True)
        return [percent_dict[p] for p in percents]

    def append(self, student):
        self.duration_info.append(student)

        if not student.nationality in self.nationality_info.keys():
            self.nationality_info[student.nationality] = []
        self.nationality_info[student.nationality].append(student)        

class YearsEnrolled:

    round_to = 1
    
    def __init__(self):
        self.years_here = {}

    def all_years(self):
        years = self.years_here.keys()
        years.sort(reverse=True)
        return years
    
    def add(self, student):
        years = str(student.years_enrolled)[0]
        if not years in self.years_here.keys():
            self.years_here[years] = YearsDatabase(years)
        self.years_here[years].append(student)

    def output(self, total):
        if not self.years_here:
            return
        all_years = self.years_here.keys()
        for year in all_years:
            database = self.years_here[year]
            how_many_total = database.how_many_duration()
            how_long = {'0': "less than a year", '1': "one year"}.get(year, '{} years'.format(year))
            percentage = round((how_many_total / total) * 100, self.round_to)
            print("\t{} kids enrolled for {} ({}%)".format(how_many_total, how_long, percentage))
            nationalities = database.nationalities()
            nationalities.sort()
            for nationality in nationalities:
                how_many = database.how_many_nationality(nationality)
                percent = round((how_many / how_many_total) * 100, self.round_to)
                print("\t\t{} of them ({}%) are from {}".format(how_many, percent, nationality))

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
        koreans = 'koreans'
        korean_middle_school = 'korean_middle_school'
        korean_high_school = 'korean_high_school'
        korean_elementary = 'korean_elementary'
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
        if not koreans in self._db.keys():
            self._db[koreans] = Breakdown("Koreans")
        if not korean_middle_school in self._db.keys():
            self._db[korean_middle_school] = Breakdown("Koreans in Middle School")
        if not korean_high_school in self._db.keys():
            self._db[korean_high_school] = Breakdown("Koreans in High School")
        if not korean_elementary in self._db.keys():
            self._db[korean_elementary] = Breakdown("Koreans in Elementary")

        self._db[target].add(student)
        if student.is_secondary:
            self._db[secondary].add(student)
            for course in student.courses():
                pass

        if student.is_korean:
            self._db[koreans].add(student)
            if student.grade in [6, 7, 8]:
                self._db[korean_middle_school].add(student)
            if student.grade in [9, 10, 11, 12]:
                self._db[korean_high_school].add(student)
            if student.is_elementary:
                self._db[korean_elementary].add(student)
                
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
