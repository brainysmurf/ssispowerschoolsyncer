from utils.Utilities import on_server

try:
    import smtplib
    import re
    import html2text
    import time
    on_server = on_server and True
except ImportError:
    on_server = False

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_unicode_aware_html_email(fromwho, towho, subject, html, ccwho=[], bccwho=[]):
    # Create message container - the correct MIME type is multipart/alternative.


    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(subject.encode('utf-8'), 'UTF-8').encode()
    pattern = '^.*<(.*?)>.*$'
    if re.match(pattern, fromwho):
        sender = re.sub(pattern, '\\1', fromwho)
    else:
        sender = fromwho
    msg['From'] = Header(fromwho.encode('utf-8'), 'UTF-8').encode()
    if isinstance(towho, list):
        temp_to = ", ".join(towho)
    else:
        temp_to = towho
    msg['To'] = Header(temp_to.encode('utf-8'), 'utf-8').encode()
    
    if ccwho:
        msg['CC'] = Header(ccwho.encode('utf-8'), 'utf-8').encode()
    tolist = []
    if isinstance(towho, list):
        tolist.extend(towho)
    else:
        tolist.append(towho)
    if isinstance(ccwho, list):
        tolist.extend(ccwho)
    else:
        tolist.append(ccwho)
    if isinstance(bccwho, list):
        tolist.extend(bccwho)
    else:
        tolist.append(bccwho)

    # Make the body of the message the same for both plain text and html.
    plaintext = html2text.html2text(html)

    # Record the MIME types of both parts - text/plain and text/html.
    part2 = MIMEText(html.encode('utf-8'), 'html', 'utf-8')
    part1 = MIMEText(plaintext.encode('utf-8'), 'plain', 'utf-8')


    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    # Need to remove unicode characters so that the string converts correctly
    #regexp = re.compile('[^\x09\x0A\x0D\x20-\x7F]')
    #msg_as_string = regexp.sub('', msg.as_string())
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, tolist, msg.as_string())
    s.quit()
    

def send_html_email(fromwho, towho, subject, html, ccwho=[], bccwho=[]):
    """
    Sends an html-compatible email
    towho can be list or just string
    fromwho can take format "Full Name <someone@example.com>", or just string
    html is automatically converted to plaintext using markdown
    """
    if not on_server:
        print("Email to be sent to {} with subject {}".format(towho, subject))
        print(html)
        return
     
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    pattern = '^.*<(.*?)>.*$'
    if re.match(pattern, fromwho):
        sender = re.sub(pattern, '\\1', fromwho)
    else:
        sender = fromwho
    msg['From'] = fromwho
    if isinstance(towho, list):
        msg['To'] = ", ".join(towho)
    else:
        msg['To'] = towho
    if ccwho:
        msg['CC'] = ccwho
    tolist = []
    if isinstance(towho, list):
        tolist.extend(towho)
    else:
        tolist.append(towho)
    if isinstance(ccwho, list):
        tolist.extend(ccwho)
    else:
        tolist.append(ccwho)
    if isinstance(bccwho, list):
        tolist.extend(bccwho)
    else:
        tolist.append(bccwho)

    # Make the body of the message the same for both plain text and html.
    plaintext = html2text.html2text(html)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(plaintext, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    # Need to remove unicode characters so that the string converts correctly
    regexp = re.compile('[^\x09\x0A\x0D\x20-\x7F]')
    msg_as_string = regexp.sub('', msg.as_string())
    #print(msg_as_string)
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, tolist, msg_as_string)
    s.quit()


if __name__ == "__main__":

    send_unicode_aware_html_email('adammorris@ssis-suzhou.net', 'adammorris@ssis-suzhou.net', 'unicode test 你好', "你好", ccwho=[], bccwho=[])
    
