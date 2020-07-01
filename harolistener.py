#!/usr/bin/python3
# default python library imports
from __future__ import print_function
import base64
import email
import pickle
import os.path
from time import sleep
from email.mime.text import MIMEText
# Google api imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# project specific imports
from inboxmanager import initInbox
from utils import getTime
from colors import *

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.settings.basic'
]

link_keywords = [
    'yoga',
    'subscription box',
    'gift guide',
    'gift list',
    'mother\'s day',
    'valentine\'s day',
    'mindfulness',
    'meditation',
]

user_email = 'jennifer@buddhiboxes.com'
notification_email = 'jennifermayfield11@gmail.com'


def messageLoop(params):
    while True:
        sleep(1800)
        print('{} Checking for messages...'.format(getTime()))
        processMessages(params)



def processMessages(params):
    service = params['service']
    user_id = params['user_id']
    label_ids = params['labels']

    try:
        response = service.users().messages().list(userId=user_id, labelIds=[label_ids['unprocessed']]).execute()
    except Exception as error:
        print('{} Error getting messages: {}'.format(getTime(), error))
        return

    if 'messages' in response:
        msg_ids = response['messages']
        print('{} Found {} messages'.format(getTime(), len(msg_ids)))
    else:
        print('{} Found 0 messages'.format(getTime()))
        return

    for ids in msg_ids:
        msg_id = ids['id']
        print('{} Processing message {}'.format(getTime(), msg_id))
        try:
            response = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
        except Exception as error:
            printFail("{} Error retrieving message with id {}: {}".format(getTime(), id, error))
            return

        msg_body = getMessageBody(response['raw'])

        found_links = findLinks(str(msg_body))
        if len(found_links) > 0:
            notification_response = notify(service, user_id, found_links)
            if not notification_response is None:
                printGreen('{} Sent message with id {}'.format(getTime(), notification_response['id']))
            else:
                printFail('{} Error sending notification'.format(getTime()))
                

        markProcessed(service, user_id, msg_id, label_ids)


def getMessageBody(body):
    msg_str = base64.urlsafe_b64decode(body.encode('ASCII'))
    mime_message = email.message_from_bytes(msg_str)
    return mime_message.get_payload(0)


def findLinks(body):
    found_links = []
    # Haro links are ended by the string below
    links_end = '****************************'
    link_num = 1
    while(1):
        start_idx = body.find('{}) '.format(link_num))
        if start_idx == -1:
            break
        body = body[start_idx:] # less to search through next iteration

        end_idx = body.find('{}) '.format(link_num+1))
        if end_idx == -1:
            end_idx = body.find(links_end)
            if end_idx == -1:
                break

        full_link = body[:end_idx]
        link_title = full_link[:full_link.find('<')].lower()
        for key in link_keywords:
            if key in link_title:
                found_links.append(full_link)
                break
        
        link_num += 1

    return found_links


def notify(service, user_id, found_links):
    encoded_msg = createMessage(found_links)
    try:
        response = service.users().messages().send(userId=user_id, body=encoded_msg).execute()
    except Exception as error:
        printFail('{} Error sending notification: {}'.format(getTime(), error))
        return None
    return response


def createMessage(found_links):
    msg_text = 'The links containing keywords are:\n'
    for link in found_links:
        msg_text += link

    message = MIMEText(msg_text)
    message['to'] = notification_email
    message['from'] = user_email
    message['subject'] = '[HaroScraper] Found {} links containing keywords'.format(len(found_links))
    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    return {'raw': raw}


def markProcessed(service, user_id, msg_id, label_ids):
    label_updates = {
        'addLabelIds': [
            label_ids['archive'],
            label_ids['processed']
        ],
        'removeLabelIds': [
            label_ids['unprocessed'],
            ['INBOX']
        ]
    }

    try:
        response = service.users().messages().modify(userId=user_id, id=msg_id, body=label_updates).execute()
    except Exception as error:
        printFail('{} Unable to mark message with id {} as processed: {}'.format(getTime(), msg_id, error))
        return None

    return response


def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    params = initInbox(service, 'me')
    params['service'] = service
    params['user_id'] = 'me'

    messageLoop(params)




if __name__ == '__main__':
    main()
