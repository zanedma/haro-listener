from __future__ import print_function
import base64
from email.mime.text import MIMEText
import os
import pickle
from time import sleep
# project specific imports
from utils import getTime, set_params, exitWithError
from colors import printGreen, printFail
import messageutils
from inboxmanager import InboxManager
# google api imports
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.settings.basic'
]


class HaroListener:
    """Manages communication with the Gmail inbox and sending the notification
    email if any links are found

    @param params Dict: Dictionary that must contain the following key/value
    pairs:
        - service Gmail service object: Has established connection to gmail
        inbox
        - user_id: Usually the string \'me\', indicating who the notification
        email message is sent from
        - link_keys List[string]: List of key words and phrases to search for
        in HARO emails
        - notification_emails string: Email address to send the notification to
        - user_email string: Email address that receives the HARO emails to be
        scrubbed
    """
    def __init__(self, params):
        assert isinstance(params, dict), 'params must be of type dict'
        # set all known parameters
        if 'service' in params:
            self.service = params['service']
        else:
            exitWithError('missing parameter service')
        if 'user_id' in params:
            self.user_id = params['user_id']
        else:
            exitWithError('missing parameter user_id')
        if 'link_keys' in params:
            self.link_keys = params['link_keys']
        else:
            exitWithError('missing parameter link_keys')
        if 'notification_emails' in params:
            self.notification_email = params['notification_emails']
        else:
            exitWithError('missing parameter notification_emails')
        if 'user_email' in params:
            self.user_email = params['user_email']
        else:
            exitWithError('missing parameter user_email')
        # set up inbox filters and labels and set their ids
        self.inbox_manager = InboxManager(self.service, self.user_id)
        ids = self.inbox_manager.initInbox()
        self.label_ids = ids['labels']
        self.filter_id = ids['filter']


    def messageLoop(self):
        """Infinite loop that checks the inbox every 30 minutes for new HARO
        emails to be processed.
        """
        while True:
            print('{} Checking for messages...'.format(getTime()))
            msg_ids = self.getMessages()
            if len(msg_ids) > 0:
                self.processMessages(msg_ids)
            sleep_time = 1800
            print('{} Sleeping for {} minutes'.format(getTime(), int(sleep_time/60)))
            sleep(1800)


    def getMessages(self):
        """Retrieve new messages to be process from the haro_unprocessed label

        @return List[message objects]: list of new messages to be processed
        """
        # needs service, user_id, label_ids
        label_id = [self.label_ids['unprocessed']]
        try:
            response = self.service.users().messages().list(userId=self.user_id, labelIds=label_id).execute()
        except Exception as error:
            printFail('{} Error getting messages: {}'.format(getTime(), error))
            return []

        if 'messages' in response:
            msg_ids = [message['id'] for message in response['messages']]
            print('{} Received {} messages'.format(getTime(), len(msg_ids)))
            return msg_ids
        
        print('{} Received 0 messages'.format(getTime()))
        return []


    def processMessages(self, msg_ids):
        """Process all the messages corresponding to the items in msg_ids for
        links containing key words/phrases specified in self.link_keys. If any
        links are found, call self.notify() to notify the notification_emails.

        @param msg_ids List[String]: msg_ids obtained from getMessages()
        """
        for msg_id in msg_ids:
            print('{} Processing message with id {}'.format(getTime(), msg_id))
            try:
                response = self.service.users().messages().get(userId=self.user_id, id=msg_id, format='raw').execute()
            except Exception as error:
                printFail("{} Error retrieving message with id {}: {}".format(getTime(), id, error))
                return

            msg_body = messageutils.getMimeMessage(response['raw'])

            found_links = messageutils.findLinks(str(msg_body), self.link_keys)
            if len(found_links) > 0:
                print('{} Found {} links containing key words/phrases'.format(getTime(), len(found_links)))
                self.notify(found_links)
            else:
                print('{} Found 0 links containing key words'.format(getTime()))

            self.inbox_manager.markProcessed(msg_id, self.label_ids)

    
    def notify(self, found_links):
        """Notify the notification_emails of the links processMessages() found.

        @param found_links List[String]: Links found containing key words/phrases
        """
        for email in self.notification_emails:
            encoded_msg = self.createMessage(found_links, email)
            try:
                response = self.service.users().messages().send(userId=self.user_id, body=encoded_msg).execute()
            except Exception as error:
                printFail('{} Error sending notification: {}'.format(getTime(), error))
                response = None
            if response is None:
                printFail('{} Error sending notification email to {}: {}'.format(getTime(), email, error))
            else:
                printGreen('{} Successfully sent notification email to {}'.format(getTime(), email))


    def createMessage(self, found_links, email):
        msg_text = 'The links containing keywords are:\n'
        links = '\n'.join(found_links)
        msg_text += links

        message = MIMEText(msg_text)
        message['to'] = email
        message['from'] = self.user_email
        message['subject'] = '[HARO Scraper] Found {} links of interest'.format(len(found_links))
        raw_message = base64.urlsafe_b64encode(message.as_bytes())
        raw_message = raw_message.decode()
        return {'raw': raw_message}


def main():
    # Establish gmail connection
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
    
    print('{} Establishing params'.format(getTime()))
    params = set_params()
    params['service'] = service
    params['user_id'] = 'HaroListener'
    printGreen('{} Successfully established params'.format(getTime()))

    listener = HaroListener(params)
    listener.messageLoop()


if __name__ == "__main__":
    main()
