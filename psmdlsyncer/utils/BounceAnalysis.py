"""

"""
import re
path_to_mail_log = '/Users/adammorris/src/ssis/mail.log'
from psmdlsyncer.settings import config_get_section_attribute, \
     define_command_line_arguments
from psmdlsyncer.html_email import Email
from psmdlsyncer.utils import NS
from collections import defaultdict
args = define_command_line_arguments('stdout', 'no_emails')
output = config_get_section_attribute('DIRECTORIES', 'path_to_output')
domain = config_get_section_attribute('EMAIL', 'domain')
if not domain:
    domain = 'localhost'
def out(line):
    with open(output + '/bounce_stats.txt', 'a') as f:
        f.write(str(line) + '\n')

class Bounce:
    def __init__(self):
        self.count = 0
        self.messages = []
        self.key = ""
    def __repr__(self):
        return self.key + ': ' + str(self.count) + '\n' + str(self.messages)
        
bounces = defaultdict(Bounce)
for line in open(path_to_mail_log):
    if "status=bounced" in line:
        match = re.search("to=<(.*?)>", line)
        if match:
            to_who = match.group(1)
            where = line.index('status=bounced')
            message = line[ (where+ len('status=bounced')+1): -1]
            match = re.search("orig_to=<(.*?)>", line)
            if match:
                orig_to = match.group(1)
                if args.stdout:
                    print(to_who)
                    print(orig_to)
                bounce = bounces[to_who]
                bounce.key = to_who
                bounce.count += 1
                bounce.messages.append(message)

email = Email(domain)
email.add_to('adammorris@ssis-suzhou.net')
email.make_subject("Bounces")
email.define_sender('DragonNet Admin <lcssisadmin@student.ssis-suzhou.net>')
html = ""
for bounce in bounces:
    ns = NS(bounces[bounce])
    ns.messages = "\n".join(ns.messages)
    html += ns('<b>{key}</b>{COLON}{SPACE}{count}{NEWLINE}<i>{messages}</i>{NEWLINE}{NEWLINE}')
    
email.define_content(html)
if not args.no_emails:
    email.send()
if args.stdout:
    print(email.htmls['en'])
