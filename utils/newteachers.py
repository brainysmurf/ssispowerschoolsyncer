"""
Uses a list to make new accounts
"""

list_of_new_usernames = ['samnjoanne@cafes.net', 'alfonsomatthew@gmail.com', 'frankbaragwanath@gmail.com', 'ruthie.bee@hotmail.com', 'mbellino@bigpond.net.au', 'lucyburden1@gmail.com', 'jcheongma@gmail.com', 'cowellemma@yahoo.co.uk', 'mrsmarrows@gmail.com', 'pacman3344@yahoo.com', 'ads_griff@hotmail.com', 'leanne.bubbard@education.tas.gov.au', 'crittercarly@yahoo.com', 'johnson.ena@gmail.com', 'mkcdrkelly@yahoo.com.au', 'mnmlinsay@hotmail.com', 'marrows.jack@gmail.com', 'sue.mckellar@hotmail.com', 'coucal@hotmail.com', 'MaryB.Panneton@yahoo.com', 'm.parratt@gmail.com', 'parratt.allison@gmail.com', 'simoner1577@gmail.com', 'wjreagin@gmail.com', 'jadams@senri.ed.jp', 'merriss.shenstone@gmail.com', 'mananeng@hotmail.com']

from Bulk import MoodleCSVFile

output_file = MoodleCSVFile('/tmp/newteachers.txt')
output_file.build_headers(['username', 'cohort_'])

for new_username in list_of_new_usernames:
    row = output_file.factory()
    row.build_username(new_username)
    row.build_cohort_(['teachersALL'])
    row.build_cohort_(['teachersSEC'])
    output_file.add_row(row)

print(output_file.output())
