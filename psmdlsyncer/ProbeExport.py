"""
Exports what is on the Probe database in easy format for teachers to look at
"""

from psmdlsyncer.utils.DB import DragonNetDBConnection

k_student_name = 18
k_percentage = 22
k_analysis = 23
k_type = 21
k_set = 20

k_record_id = -1 #last item
k_field_id = 3
k_content = 2

class ProbeDB(DragonNetDBConnection):
    def __init__(self):
        super().__init__()
        self.raw = self.sql("select distinct usr.firstname, usr.lastname, dc.content, dc.fieldid, dc.recordid from ssismdl_data_content dc " +
                            "join ssismdl_data_records dr on dc.recordid = dr.id " +
                            "join ssismdl_user usr on dr.userid = usr.id " +
                       "join ssismdl_data_fields df on dc.fieldid = df.id " + "join ssismdl_data d on df.dataid = 4 order by dc.recordid")()

        record_ids = []
        for line in self.raw:
            r_id = line[k_record_id]
            if not r_id in record_ids:
                record_ids.append( r_id )

        final = {}
        
        for record_id in record_ids:

            this_entry = [ i for i in self.raw if i[k_record_id] == record_id ]
            if this_entry:
               entry = {}
               entry['teacher'] = this_entry[0][0] + " " + this_entry[0][1]
               for row in this_entry:
                   field_id = row[k_field_id]
                   if field_id == k_student_name:
                       entry['student'] = row[k_content]
                   elif field_id == k_percentage:
                       entry['percent'] = row[k_content]
                   elif field_id == k_analysis:
                       entry['analysis'] = ', '.join(row[k_content].split('##')) if row[k_content] else "NOT ENTERED!"
                   elif field_id == k_type:
                       entry['type'] = row[k_content]
                   elif field_id == k_set:
                       entry['set'] = row[k_content]
           
               if not entry['teacher'] in list(final.keys()):
                   final[entry['teacher']] = []

               final[entry['teacher']].append( entry )
                   
        for teacher in final:
            with open('../output/probe/{}.txt'.format(teacher), 'w') as f:
                entries = final[teacher]
                entries.sort(key=lambda x: x['student'])
                for entry in entries:
                    f.write(entry['student']+ '\n')
                    f.write("\tSet:      {}\n".format(entry['set']))
                    f.write("\tPercent:  {}\n".format(entry['percent']))
                    f.write("\tAnalysis: {}\n".format(entry['analysis']))
                    f.write("\tType:     {}\n".format(entry['type']))
                    f.write('\n')



if __name__ == "__main__":

    probe = ProbeDB()
    
    
