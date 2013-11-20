from psmdlsyncer.settings import config_get_section_attribute

user = """usebccparentsALL.txt
usebccparentsCHINESE.txt
usebccparentsELEM.txt
usebccparentsKOREAN.txt
usebccparentsSEC.txt"""


def put_in_order(what, reverse=False):
    what = what.upper()
    result = 1 # elementary don't have LEARN
    if reverse:
        trans = {'L':8,'E':7,'A':6,'R':5,'N':4,'S':3,'SWA':2,'JS':1}
    else:
        trans = {'L':1,'E':2,'A':3,'R':4,'N':5,'S':6,'SWA':7, 'JS':8}
    if '6' in what:
        result = 100 + trans[re.sub('[0-9]', '', what)]
    elif '7' in what:
        result =  200 + trans[re.sub('[0-9]', '', what)]
    elif '8' in what:
        result =  300 + trans[re.sub('[0-9]', '', what)]
    elif '9' in what:
        result =  400 + trans[re.sub('[0-9]', '', what)]
    elif '10' in what:
        result = 500 + trans[re.sub('[0-9]', '', what)]
    elif '11' in what:
        result = 600 + trans[re.sub('[0-9]', '', what)]
    elif '12' in what:
        result = 700 + trans[re.sub('[0-9]', '', what)]
    elif re.sub('[1..9]', '', what):
        result = ord(re.sub('[1..9]', '', what)[0])
    return result

area = config_get_section_attribute('EMAIL', 'aliases_path')
area += '/homerooms'

import os
user = os.listdir(area)

for item in user:
    item = item.strip()
    item = item.replace('.txt', '@student.ssis-suzhou.net')
    item = '<a href="mailto:?bcc={0}">{0}</a><br />'.format(item)
    print(item)
