from psmdlsyncer.settings import config_get_section_attribute
import datetime
import re

output = config_get_section_attribute('DIRECTORIES', 'path_to_output')
def out(line):
    with open(output + '/mail_stats.txt', 'a') as f:
        f.write(str(line) + '\n')

today = datetime.datetime.today().strftime('%b %d')
out("-----------")
out(today)
students = {}
pop3 = {}
imap = {}
count = 0
with open('/var/log/dovecot.log') as f:
        for line in f:
                if re.match(r'^'+today, line):
                        userinfo = re.sub(r'^(.*?)Login: user=<', '', line)
                        userinfo = re.sub(r'>.*', '', userinfo)
                        userinfo = userinfo.strip('\n').strip()
                        if not ' ' in userinfo:
                                if not userinfo in students:
                                        students[userinfo] = 0
                                students[userinfo] += 1

                                pop = re.match(r'.* pop3.*', line)
                                if pop:
                                        if not userinfo in list(pop3.keys()):
                                                pop3[userinfo] = 0
                                        pop3[userinfo] += 1

                                imp = re.match(r'.* imap.*', line)
                                if imp:
                                        if not userinfo in list(imap.keys()):
                                                imap[userinfo] = 0
                                        imap[userinfo] += 1

sort_list = []

out("Number of students successfully accessing:")
out(len(list(students.keys())))

for student in list(students.keys()):
        sort_list.append( (student, students[student])  )

count = 0
s = ""
sort_list.sort(key=lambda x: x[1], reverse=True)
for item in sort_list:
        if item[1] > 100:
                count += 1
                s += "{} : {}\n".format(item[0], item[1])
out("There are {} students with over 100 accesses".format(count))
out(s)

out("There are {} students using Apple Mail".format(len(list(pop3))))
out(pop3)
out("There are {} studnets using Squirrel Mail".format(len(list(imap))))
out(imap)
