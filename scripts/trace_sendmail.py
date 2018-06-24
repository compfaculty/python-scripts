# -*- coding: utf-8 -*-
#! /usr/bin/python

__author__ = 'aum'

'''
Sends traceroute to email
'''
import os
import subprocess
import smtplib
import sys
import tempfile
import datetime
import logging

from smtplib import SMTPHeloError,SMTPAuthenticationError,SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os.path as p
import json
logging.basicConfig(format='%(asctime)-10s %(levelname)-5s:%(message)s', level=logging.DEBUG)

DEBUG=True
#if True we use TemporaryFile, else we create log file in user root dir
TEMPORARYFILE = True 
#log file path(if we not using TemporaryFile)
LOG_FILE = p.join(p.expanduser('~'),'traceback.txt')
#Set here end point traceroute 
TO_SERVER = 'ukr.net'    

#TODO rework auth mechanism 
def _get_credentials(fn='auth.json'):
    
    #1. trying to read from fn
    
    try:
        try:
            curdir = p.dirname(p.realpath(__file__))
            filepath = p.join(curdir,fn)
            with open(filepath,'r') as fname:
                auth = json.load(fname)
        except IOError:
            
            #2. trying to read from environ, you need to set these values (i.e in .bashrc)
            import operator
             
            auth = dict([operator.itemgetter('USER_EMAIL','USER_PASS')(os.environ)])
    
    except KeyError:      
        raise Exception('Cant find credentials')
        
    if not auth: raise Exception('Cant find credentials')
        
    else:
        return auth        

LOGIN, PASS = _get_credentials().popitem()              

def create_mime_message(from_, to_,
                        subject_='Route Info: {0}'.format(' '.join(os.uname())) ,
                        preamble_='route log',
                        info_file=''):
    '''Create the container (outer) email message.'''
    try:
        msg = MIMEMultipart()
        msg['Subject'] = subject_
        msg['From'] = from_ #email address sending from
        msg['To'] = to_ #email address sending to
        msg.preamble = preamble_
        #attach user file to message
        try:
            assert not info_file.closed 
            info_file.seek(0)
            loginfo = MIMEText(info_file.read())
            msg.attach(loginfo)
        finally : 
            info_file.close()     
    except Exception:
        print sys.exc_info()
    else: return msg

def send_gmail(login, passwd, mime_message, smtp_server_port='smtp.gmail.com:587'):
    """sending mail  to gmail"""
    try:
        server = smtplib.SMTP(smtp_server_port)
        server.starttls()
        server.login(login,passwd)
        server.sendmail(mime_message.get('From'),mime_message.get('To'), mime_message.as_string())

    except SMTPHeloError as e:
        logging.error("Error code {0}, Error mesage {1}".format(e.smtp_code, e.smtp_error))
        return False
    except SMTPAuthenticationError as e:
        logging.error("Error code {0}, Error mesage {1}".format(e.smtp_code, e.smtp_error))
        return False
    except SMTPException as e:
        logging.error("Error code {0}, Error mesage {1}".format(e.smtp_code, e.smtp_error))
        return False
    else:
        if DEBUG: logging.info("Trace is sent!")
        return True
    finally: server.quit()

#TODO need to check or sudo apt-get install traceroute
def send_trace_to_owner():
    
    f = tempfile.TemporaryFile() if TEMPORARYFILE else open(LOG_FILE,'w')  
    subprocess.call(['traceroute', TO_SERVER], stdout=f)
    f.write("-----------{0:%x-%X}-------------".format(datetime.datetime.now()))
    mime_msg = create_mime_message(
        from_= LOGIN,
        to_= LOGIN,
        info_file=f)
    res = False
    while not res:
        res = send_gmail(
                login=LOGIN,
                passwd=PASS,
                mime_message=mime_msg
                )


if __name__ == "__main__":
    
    send_trace_to_owner()
    if DEBUG: logging.info("Done")    