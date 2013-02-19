"""
Exports what is on the Probe database in easy format for teachers to look at
"""

from utils.DB import DragonNetDBConnection

k_record_id = -1 #last item
k_field_id = 3
k_content = 2

k_dataid = 19    # you should get this number by looking in the database: select name, id from ssismdl_data;
k_activity_name =151
k_venue = 156
k_description = 161

import re

def strip_html(html):
    html = re.sub(r'<\s*\w.*?>', '', html)  # removes any start tags
    html = re.sub(r'<\s*\/\s*\w\s*.*?>|<\s*br\s*>', '', html)  # removes any end tags
    return html

def quote(s, comma=True):
    s = '"{}"'.format(s)
    if comma:
        return s + ','
    else:
        return s
    
def paragraphize(s):
    result = ""
    for frag in s.split('\r\n'):
        if not frag.strip():
            frag = " "
        result += frag
    return result

class ProbeDB(DragonNetDBConnection):
    def __init__(self):
        super().__init__()
        self.raw = self.sql("select distinct usr.firstname, usr.lastname, dc.content, dc.fieldid, dc.recordid from ssismdl_data_content dc " +
                            "join ssismdl_data_records dr on dc.recordid = dr.id " +
                            "join ssismdl_user usr on dr.userid = usr.id " +
                       "join ssismdl_data_fields df on dc.fieldid = df.id " + "join ssismdl_data d on df.dataid = {} order by dc.recordid".format(k_dataid))()

        record_ids = []
        for line in self.raw:
            r_id = line[k_record_id]
            if not r_id in record_ids:
                record_ids.append( r_id )

        entries = []
       
        for record_id in record_ids:

            this_entry = [ i for i in self.raw if i[k_record_id] == record_id ]
            if this_entry:
               entry = {}
               entry['user'] = this_entry[0][0] + " " + this_entry[0][1]
               for row in this_entry:
                   field_id = row[k_field_id]
                   if field_id == k_activity_name:
                       entry['activity_name'] = row[k_content]
                   elif field_id == k_venue:
                       entry['venue'] = row[k_content]
                   elif field_id == k_description:
                       entry['desc'] = row[k_content]           
               entries.append( entry )

        with open('../output/activities.txt', 'w') as f:
            f.write("Activity Name, Staff, Venue, Description\n")
            for entry in entries:
                if not entry:
                    continue
                f.write(quote(paragraphize(entry['activity_name'])))
                f.write(quote(entry['user']))
                f.write(quote(paragraphize(entry['venue'])))
                f.write(quote(  paragraphize( strip_html(entry['desc']) ), comma=False)  )
                f.write("\n")



if __name__ == "__main__":

    probe = ProbeDB()
    
    
