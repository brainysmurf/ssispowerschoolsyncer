"""
Exports what is on the Probe database in easy format for teachers to look at
"""

from psmdlsyncer.utils.DB import DragonNetDBConnection
from psmdlsyncer.utils.Formatter import Smartformatter
from collections import defaultdict
import datetime
import re

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

class ProbeDB(DragonNetDBConnection):
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
        
        for record_id in record_ids:

            this_entry = [ i for i in self.raw if i[k_record_id] == record_id ]
            if this_entry:
                entry = Smartformatter()
                entry.teacher = this_entry[0][0] + " " + this_entry[0][1]
                entry.date = timestamp_to_python_date(this_entry[0][2])
                entry.date_entered = entry.date.strftime('%m/%d/%Y')
                entry.test_date = {2012:'10/15/2012', 2013:'5/15/2013'}.get(entry.date.year)
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
                entry.differential = -1

                teachers[entry.teacher].append( entry )
                powerschool.append( entry('{powerschoolid}{TAB}{test_date}{TAB}{grade}{TAB}{set}{TAB}{percent}{TAB}{type}{TAB}{analysis}{TAB}{differential}') )

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
    
    
