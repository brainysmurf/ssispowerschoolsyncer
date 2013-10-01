"""
Exports what is on the Probe database in easy format for teachers to look at
"""

from psmdlsyncer.sql import MoodleDBConnection
from psmdlsyncer.utils.Namespace import NS
from collections import defaultdict
import datetime
import re

def make_date(year, month, day):
    return datetime.datetime(year, month, day)

reading_age_from_set = {'Set 0':4,  # SET 0 IS WHAT READING AGE THEN?
                        'Set 1':5.5,
                        'Set 2':6.0,
                        'Set 3':6.5,
                        'Set 4':7.0,
                        'Set 5':7.5,
                        'Set 6':8.0,
                        'Set 7':8.5,
                        'Set 8':9.0,
                        'Set 9':9.5,
                        'Set 10':10.0,
                        'Set 11':10.5,
                        'Set 12':11.0,
                        'Set 13':11.5,
                        'Set 14':12.0,
                        'Set 15':12.5,
                        'Set 16':13.0,
                        'Set 17':13.5,
                        'Set 18':14.0,
                        'Set 19':14.5,
                        'Set 20':15.0}

k_student_name = 18
k_percentage = 22
k_analysis = 23
k_type = 21
k_set = 20

k_record_id = -1 #last item
how_many_common_items = 3

# AWKWARD, HAVE TO CALCULATE THE FIELD
k_field_id = how_many_common_items + 1
k_content = how_many_common_items

def timestamp_to_python_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)

from psmdlsyncer.Students import Students

class ProbeDB(MoodleDBConnection):
    def __init__(self):
        super().__init__()
        self.raw = self.sql("select distinct usr.firstname, usr.lastname, dr.timecreated, dc.content, dc.fieldid, dc.recordid from ssismdl_data_content dc " +
                            "join ssismdl_data_records dr on dc.recordid = dr.id " +
                            "join ssismdl_user usr on dr.userid = usr.id " +
                       "join ssismdl_data_fields df on dc.fieldid = df.id " + "join ssismdl_data d on df.dataid = 4 order by dc.recordid")()

        record_ids = []
        for line in self.raw:
            r_id = line[k_record_id]
            if not r_id in record_ids:
                record_ids.append( r_id )

        teachers = defaultdict(list)
        powerschool = ['Student_Number\tTest_Date\tGrade_Level\tReading_Age_1\tScore_2\tCategory_3\tIndications_3\tDifferential_1']

        student_info = Students()
        
        for record_id in record_ids:

            this_entry = [ i for i in self.raw if i[k_record_id] == record_id ]
            if this_entry:
                entry = NS()
                entry.teacher = this_entry[0][0] + " " + this_entry[0][1]
                entry.date = timestamp_to_python_date(this_entry[0][2])
                entry.date_entered = entry.date.strftime('%m/%d/%Y')
                entry.test_date = {2012:make_date(2012, 10, 15), 2013:make_date(2013, 5, 15)}.get(entry.date.year)
                entry.test_date_output = entry.test_date.strftime('%m/%d/%Y')
                for row in this_entry:
                    field_id = row[k_field_id]
                    if field_id == k_student_name:
                        entry.student = row[k_content]
                        entry.powerschoolid = entry.student
                        match = re.search( '\((.*) (.*)\)', entry.student)
                        if match:
                            entry.homeroom, entry.powerschoolid = match.groups()
                            entry.grade = re.sub('[A-Z]', '', entry.homeroom)
                        else:
                            entry.homeroom = ''
                            entry.grade = -1
                    elif field_id == k_percentage:
                        entry.percent = row[k_content]
                    elif field_id == k_analysis:
                        entry.analysis = ', '.join(row[k_content].split('##')) if row[k_content] else ""
                    elif field_id == k_type:
                        entry.type = row[k_content]
                    elif field_id == k_set:
                        entry.set = row[k_content]
                        entry.reading_age = reading_age_from_set.get(entry.set)

                student_info.get_student(entry.powerschoolid)
                entry.age = float((entry.test_date - birthdate).days) / 365.25
                entry.differential = entry.reading_age

                teachers[entry.teacher].append( entry )
                powerschool.append( entry('{powerschoolid}{TAB}{test_date_output}{TAB}{grade}{TAB}{reading_age}{TAB}{percent}{TAB}{type}{TAB}{analysis}{TAB}{differential}') )

        with open('../../output/probe/powerschool.txt', 'w') as f:
            f.write( "\n".join(powerschool) )

        for teacher in teachers:
            with open('../../output/probe/{}.txt'.format(teacher), 'w') as f:
                entries = teachers[teacher]
                entries.sort(key=lambda x: x.student)
                for entry in entries:
                    f.write(entry.student+ '\n')
                    f.write("\tSet:      {}\n".format(entry.set))
                    f.write("\tPercent:  {}\n".format(entry.percent))
                    f.write("\tAnalysis: {}\n".format(entry.analysis))
                    f.write("\tType:     {}\n".format(entry.type))
                    f.write('\n')



if __name__ == "__main__":

    probe = ProbeDB()
    
    
