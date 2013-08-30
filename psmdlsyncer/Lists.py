from psmdlsyncer.Students import Students
from psmdlsyncer.utils.Formatter import Smartformatter
from psmdlsyncer.utils.Bulk import MoodleCSVFile

from settings import config_get_section_attribute

def student_list_for_CAS():
    students = Students()

    results = []

    for student_key in students.get_student_keys():
        student = students.get_student(student_key)
        if not student.is_secondary:
            continue
        if student.grade == 12:
            continue
        sf = Smartformatter(newline='\n', comma=',', space=" ",
                            left='(', right=')')
        sf.take_dict(student)
        results.append(sf("{homeroom}:{space}{first}{space}{last}{space}{left}{num}{right}{newline}"))

    results.sort()

    with open(config_get_section_attribute('DIRECTORIES', 'path_to_output') + '/' + 'all_students', 'w') as f:
        for item in results:
            f.write(item)


def student_list_for_cohorts():

    students = Students()
    path_to_output = config_get_section_attribute('DIRECTORIES', 'path_to_output')
    output_file = MoodleCSVFile(path_to_output + '/' + 'required_cohort_enrollments.txt')
    output_file.build_headers(['username', 'firstname', 'lastname', 'cohort_'])
    
    for student_key in students.get_student_keys():
        student = students.get_student(student_key)

        if student.is_secondary:
            row = output_file.factory()
            row.build_username(student.username)
            row.build_firstname(student.first)
            row.build_lastname(student.last)
            row.build_email(student.email)
            cohorts = ['studentsALL']
            cohorts.extend(['studentsSEC'])
            if student.grade in range(9, 13):
                cohorts.extend(['studentsHS'])
            else:
                cohorts.extend(['studentsMS'])
            row.build_cohort_( cohorts )

            output_file.add_row(row)

        output_file.output()


if __name__ == "__main__":

    student_list_for_cohorts()
