from Students import Students

class SortFunc:

    def __init__(self):
        self.current = None
        self.now = None
        self._did_process = []

    def yes(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self.yes(*args, **kwargs)

class MiddleSchoolOnlyFunc(SortFunc):

    def yes(self, student):
        if student.grade in [6, 7, 8]:
            if not student.homeroom == self.now:
                self.output_header(student.homeroom)
            self.now = student.homeroom
            return True
        else:
            return False

    def output_header(self, hr):
        print("\nHomeroom {}".format(hr))

def generate(func, pre=None):
    students = Students()
    results = []
    for student in students.student_keys_by_secondary_homerooms():
        
        # Throw it to func, but func can be any structure
        # Could be a list, or something else not callable
        # Handle appropriately
        if not callable(func):
            for f in func:
                if callable(f) and f(student):
                    yield student
        elif callable(func) and func(student):
            yield student

    results.sort()
    print("\n".join(results))


if __name__ == "__main__":

    middle_school_func = MiddleSchoolOnlyFunc()
    for student in generate(middle_school_func):
        print(student.first, student.last, student.homeroom)
    
