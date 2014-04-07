import csv
from psmdlsyncer.sql import MoodleDBConnection

moodle = MoodleDBConnection()
usernames = []

def main():
    with open('list.txt') as f:
        content = csv.reader(f, delimiter='\t')
        for row in content:
            if content.line_num != 1:
                last, first, num, email = row
                username, _ = email.split('@')
                usernames.append(username)
                user = moodle.get_table('user', 'id, idnumber', username=username)
                if user:
                    if len(user) > 1:
                        print(username)
                    _id, idnumber = user[0]
                    if not idnumber:
                        moodle.update_table('user',
                            idnumber=num,
                            where=dict(username=username)
                            )

    all_teachers = moodle.call_sql("select idnumber, username from ssismdl_user where email like '%@ssis-suzhou.net'")
    for teacher in all_teachers:
        idnumber, username = teacher
        if not username in usernames:
            print(username)


main()
