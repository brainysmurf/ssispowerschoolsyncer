from Students import Students
from utils.Formatter import Smartformatter
import datetime

import re

def put_in_order(what, reverse=False):
    what = what.homeroom
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


if __name__ == "__main__":

    students = Students()

    result = []
    for student_key in students.get_student_keys():
        student = students.get_student(student_key)
        sf = Smartformatter()
        sf.take_dict(student)
        new = datetime.datetime(2013, 8, 1)
        student.last, student.first = student.lastfirst.split(', ')

        if student.is_secondary:
            result.append(student)

    result.sort(key=put_in_order)
    for student in result:
        sf = Smartformatter()
        sf.take_dict(student)
        if student.is_new_student:
            print(sf('<b>{homeroom}\t{lastfirst}\t{num}\t{username}</b><br/>'))
        else:
            print(sf('{homeroom}\t{lastfirst}\t{num}\t{username}<br/>'))
        #print(sf('{num},{first},{last},{email},{grade},IBDP,SSIS Class of 2015 (Grade 11)'))

    """
    for student in result:
        sf = Smartformatter()
        sf.take_dict(student)
        print(sf('{num},{first},{last},{email},{grade},IBDP,SSIS Class of 2015 (Grade 11)'))
    """
            
