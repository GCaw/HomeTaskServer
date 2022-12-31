import logging
import requests
import mysql.connector
import smtplib

from tasks.config import LOCAL_SQL_USERNAME, LOCAL_SQL_PASSWORD, LOCAL_DATABSE
from tasks.config import MAIL_SMTP_SERVER, MAIL_SMTP_PORT, MAIL_USERNAME, MAIL_PASSWORD

def IssueHttpRequest(call):
    retry = 3
    while(retry):
        retry -=1
        try: 
            r = requests.get(call, timeout=10)
            
            if (r.status_code == 200):
                retry = 0
            else:
                r = None

        except (requests.ConnectionError, requests.ReadTimeout) as err:
            r = None

    return r
    
def IssueSqlRequest(request):    
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user=LOCAL_SQL_USERNAME,
            passwd=LOCAL_SQL_PASSWORD,
            database=LOCAL_DATABSE
        )

        mycursor = mydb.cursor()
        mycursor.execute(request)
        res = mycursor.rowcount
    except Exception as e:
        logging.error(f"SQL Request error: {e}")
        res = None

    return res

def SelectSqlRequest(request):
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user=LOCAL_SQL_USERNAME,
            passwd=LOCAL_SQL_PASSWORD,
            database=LOCAL_DATABSE
        )

        mycursor = mydb.cursor()
        mycursor.execute(request)
        res = mycursor.fetchall()

    except Exception as e:
        logging.error(f"SQL Request error: {e}")
        res = None

    return res

def SendMail(recipient, subject, content):
    try:     
        #Create Headers
        headers = ["From: " + MAIL_USERNAME, "Subject: " + subject, "To: " + recipient,
                    "MIME-Version: 1.0", "Content-Type: text/html"]
        headers = "\r\n".join(headers)

        #Connect to Gmail Server
        session = smtplib.SMTP(MAIL_SMTP_SERVER, MAIL_SMTP_PORT)
        session.ehlo()
        session.starttls()
        session.ehlo()

        #Login to Gmail
        session.login(MAIL_USERNAME, MAIL_PASSWORD)

        #Send Email & Exit
        session.sendmail(MAIL_USERNAME, recipient, headers + "\r\n\r\n" + content)
        session.quit
        res = True

    except Exception as e:
        logging.error(f"Error sending email: {e}")
        res = None

    return res
