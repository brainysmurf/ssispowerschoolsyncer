import json
import cx_Oracle
import argparse

connection = cx_Oracle.connect('psnavigator', 'Venus_2_psn' , '(DESCRIPTION=(ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(HOST = 192.168.1.165)(PORT = 1521)))(CONNECT_DATA=(SID=PSPRODDB)))')
cursor = connection.cursor()
#cursor.execute('select table_name from all_tables order by table_name')
#cursor.execute('select * from (select * from STUDENTS) where rownum <= 1')
#cursor.execute('select * from all_tables where table_name = \'STUDENTS\'')

cursor.execute('select STUDENT_NUMBER from STUDENTS')

rows = [];

for row in cursor:
    rows.append( row );

connection.close();

#print(rows);

print( json.dumps(rows) );
