from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from utils import getTime, exitWithError
import colors


class InboxManager:
    """Gets the necessary label and filter ids for HaroScrubber and creates them if needed

        @param service connected Gmail service
        @param user_id user_id to use for requests
    """
    def __init__(self, service, user_id):
        self.service = service
        self.user_id = user_id
        self.needed_labels = {
            'unprocessed': 'haro_unprocessed',
            'processed': 'haro_processed'
        }
        # self.haro_email = 'haro@helpareporter.com'
        self.haro_email = 'zanedma@gmail.com'


    def initInbox(self):
        """Initialize the inbox and return the label and filter ids

            @return Dictionary with label ids and filter id
        """
        print('{} Initializing setup...'.format(getTime()))
        print('{} Initializing Labels...'.format(getTime()))
        labels = self.initLabels()
        print('{} Initializing Filter...'.format(getTime()))
        filter_id = self.initFilter(labels['unprocessed'])
        colors.printGreen('{} Setup complete!'.format(getTime()))
        return {'labels': labels, 'filter': filter_id}


    def initLabels(self):
        """Check if the inbox has the necessary labels, if so return the corresponding label ids.
        If not, create the labels, and return the created ids.

        @return dictionary with keys as label names and values as label ids
        """
        try:
            response = self.service.users().labels().list(userId=self.user_id).execute()
        except Exception as error:
            exitWithError(error)

        labels = response['labels']
        labels_dict = {
            'archive': None,
            'unprocessed': None,
            'processed': None
        }

        for label in labels:
            if label['name'] == '[Imap]/Archive':
                labels_dict['archive'] = label['id']
            elif label['name'] == self.needed_labels['unprocessed']:
                labels_dict['unprocessed'] = label['id']
            elif label['name'] == self.needed_labels['processed']:
                labels_dict['processed'] = label['id']

        if labels_dict['archive'] is None:
            exitWithError('Inbox does not have an archive label')

        if labels_dict['unprocessed'] is None:
            unprocessed_id = self._createLabel(self.needed_labels['unprocessed'])
            labels_dict['unprocessed'] = unprocessed_id

        if labels_dict['processed'] is None:
            processed_id = self._createLabel(self.needed_labels['processed'])
            labels_dict['processed'] = processed_id

        return labels_dict


    def initFilter(self, label_id):
        """Check if the inbox has a filter that sends emails from haro_email to the corresponding
        label. If the filter is not set up, create one or modify an existing one.

        @return filter id for corresponding filter
        """
        try:
            response = self.service.users().settings().filters().list(userId=self.user_id).execute()
        except Exception as error:
            exitWithError(error)

        filters = response['filter']

        for filter_obj in filters:
            if filter_obj['criteria']['from'] == self.haro_email:
                if not label_id in filter_obj['action']['addLabelIds']:
                    filter_obj['action']['addLabelIds'].append(label_id)
                return filter_obj['id']

        return self._createFilter(label_id)


    def _createLabel(self, label_name):
        """Create a label with the name corresponding to label_name.

        @param label_name name for the new label
        @return id of newly created label
        """
        label_obj = {
            'messageListVisibility': 'show',
            'name': label_name,
            'labelListVisibility': 'labelShow'
        }

        try:
            created_label = self.service.users().labels().create(userId=self.user_id, body=label_obj).execute()
        except Exception as error:
            exitWithError(error)

        print('{} Created label with name {}, and id {}'.format(getTime(), created_label['name'], created_label['id']))
        return created_label['id']


    def _createFilter(self, label_id):
        """Create a filter that filters emails from haro_email into label corresponding to
        label_id. 

        @param label_id id of label to filter messages into
        @return id of newly created filter
        """
        filter_obj = {
            'id': 'haro_filter',
            'criteria': {
                'from': self.haro_email,
            },
            'action': {
                'addLabelIds': label_id
            }
        }

        try:
            created_filter = self.service.users().settings().filters().create(userId=self.user_id, body=filter_obj).execute()
        except Exception as error:
            exitWithError(error)

        return created_filter['id']


    def markProcessed(self, msg_id, label_ids):
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
            response = self.service.users().messages().modify(userId=self.user_id, id=msg_id, body=label_updates).execute()
        except Exception as error:
            colors.printFail('{} Unable to mark message with id {} as processed: {}'.format(getTime(), msg_id, error))
            return None

        return response
        