from psmdlsyncer.Students import Students



def bulk_emails_info(students):
   grades = students.get_all_grades()
   grades.sort()
   with open('../dissemination/usebccaccounts.txt', 'a') as f:
      f.write('To email...\n\n')
      for grade in grades:
         d = {'grade': grade}
         d['email'] = 'usebccstudents{}@student.ssis-suzhou.net'.format(grade)
         f.write("...every student in grade {grade}, use\n{email}\n\n".format(**d))

   grades = students.get_all_grades()
   grades.sort()
   with open('../dissemination/usebccaccounts.txt', 'w') as f:
      f.write('To email...\n\n')
      for grade in grades:
         d = {'grade': grade}
         d['email'] = 'usebccparents{}@student.ssis-suzhou.net'.format(grade)
         f.write("...every parent who has a child in grade {grade}, use\n{email}\n\n".format(**d))

   homerooms = students.get_secondary_homerooms()
   print(homerooms)
   with open('../dissemination/usebccaccounts.txt', 'a') as f:
      f.write('To email...\n\n')
      for homeroom in homerooms:
         d = {'homeroom': homeroom}
         d['email'] = 'usebccstudents{}@student.ssis-suzhou.net'.format(homeroom)
         f.write("...every student in homeroom {homeroom}, use\n{email}\n\n".format(**d))

   homerooms = students.get_secondary_homerooms()
   print(homerooms)
   with open('../dissemination/usebccaccounts.txt', 'a') as f:
      f.write('To email...\n\n')
      for homeroom in homerooms:
         d = {'homeroom': homeroom}
         d['email'] = 'usebccparents{}@student.ssis-suzhou.net'.format(homeroom)
         f.write("...every parent who has a child in homeroom {homeroom}, use\n{email}\n\n".format(**d))


if __name__ == "__main__":

   students = Students()
   bulk_emails_info(students)
