from psmdlsyncer.settings import config_get_section_attribute
from psmdlsyncer.sql import MoodleDBConnection
import postgresql
import datetime
convert = datetime.datetime.fromtimestamp

output = config_get_section_attribute('DIRECTORIES', 'path_to_output')
def out(line):
    with open(output + '/account_stats.txt', 'a') as f:
        f.write(str(line) + '\n')

out(datetime.datetime.now())

has = 0
cannot = 0
last_week = 0
last_month = 0
oneweekago = datetime.datetime.today() - datetime.timedelta(days=7)
onemonthago = datetime.datetime.today() - datetime.timedelta(days=30)
dnet = MoodleDBConnection()
raw = dnet.call_sql("select lastaccess,lastlogin,idnumber from ssismdl_user where idnumber like '%P' and deleted=0")
total = len(raw)

for line in raw:
        lastaccess, lastlogin, idnumber = line
        lastaccess_date = convert(lastaccess)
        lastlogin_date  = convert(lastlogin)
        if lastaccess and not lastlogin:
                cannot += 1
        if lastlogin:
                has += 1
        if lastlogin_date > oneweekago:
                last_week += 1
        if lastlogin_date > onemonthago:
                last_month += 1
out("{} total DragonNet parent accounts".format(total))
out("{} ({}%) have successfully logged in".format(has, round((has / total) * 100,1)))
out("{} ({}%) have tried but cannot log in".format(cannot, round((cannot / total) * 100, 1)))
out("{} ({}%) have logged in within the last week".format(last_week, round((last_week / total) * 100, 1)))
out("{} ({}%) have logged in within the last month".format(last_month, round((last_month / total) * 100, 1)))
out('---------')

