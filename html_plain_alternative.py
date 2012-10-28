#!/usr/bin/env python

import smtplib
import re

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# me == my email address
# you == recipient's email address
me = "peterfowles@ssis-suzhou.net"
you = "peterfowles@ssis-suzhou.net"
#you = "adammorris@ssis-suzhou.net"

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = open('pg_subject_output').readlines()[0].strip('\n')
msg['From'] = me
msg['To'] = you

# Create the body of the message (a plain-text and an HTML version).
text = "Today's announcements"
html = "\n".join([l.strip('\n') for l in open('pg_html_output').readlines()])

# Record the MIME types of both parts - text/plain and text/html.
part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)
msg.attach(part2)

# Send the message via local SMTP server.
s = smtplib.SMTP('localhost')
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
regexp = re.compile('[^\x09\x0A\x0D\x20-\x7F]')
msg_as_string = regexp.sub('', msg.as_string())
s.sendmail(me, you, msg_as_string)
s.quit()
