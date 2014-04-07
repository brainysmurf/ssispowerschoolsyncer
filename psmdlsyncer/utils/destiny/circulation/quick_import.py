import csv
from psmdlsyncer.sql.MoodleDatabase import MoodleDBConnection
import re

# these are transformations done to the original data
remove_everything_except_digits = lambda x: re.sub("[^0-9]","", x)
barcode_transform = lambda x: x[2:] if x.startswith('P ') else x
nadda = lambda x: x
escape_quotes = lambda x: x.replace("'", '')
transform = {
    0: nadda,
    1: barcode_transform,               # barcode
    2: remove_everything_except_digits, # grade level
    3: nadda,                           # homeroom
    4: nadda,                           # transaction
    5: nadda,
    6: nadda,
    7: nadda,
    8: nadda,
    9: escape_quotes,                   # title_description
    10: nadda,
    11: nadda,
    12: nadda,
    13: nadda,
    14: nadda
}

moodle = MoodleDBConnection()
# class Moodle:
#     def insert_table(self, table, **dictionary):
#         print(dictionary)
# moodle = Moodle()

with open('circulation_report.csv', 'rU', encoding='mac-roman') as _file:
    info = csv.reader(_file)
    first_row = None
    for row in info:
        if info.line_num == 1:
            first_row = [column.lower().replace(' ', '_').replace('/', '_') for column in row]
            continue

        d = {}

        for i in range(len(first_row)):
            d[first_row[i]] = transform[i](row[i])

        moodle.insert_table(
            'ssismdl_dnet_destiny_imported',
            **d
            )

