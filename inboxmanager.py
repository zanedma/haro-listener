from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from utils import getTime, exitWithError
import colors

# Labels that need to be present/will be created in user's inbox
needed_labels = {
    'unprocessed': 'haro_unprocessed',
    'processed': 'haro_processed'
}
haro_email = 'haro@helpareporter.com'

def initInbox(service, user_id):
    print('{} Initializing setup...'.format(getTime()))
    print('{} Initializing Labels...'.format(getTime()))
    labels = _initLabels(service, user_id)
    print('{} Initializing Filter...'.format(getTime()))
    filter_id = _initFilter(service, user_id, labels['unprocessed'])
    colors.printGreen('[+] Setup complete!')
    return {'labels': labels, 'filter': filter_id}


def _initLabels(service, user_id):
    try:
        response = service.users().labels().list(userId=user_id).execute()
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
        elif label['name'] == needed_labels['unprocessed']:
            labels_dict['unprocessed'] = label['id']
        elif label['name'] == needed_labels['processed']:
            labels_dict['processed'] = label['id']

    if labels_dict['archive'] == None:
        exitWithError('Inbox does not have an archive label')
    
    if labels_dict['unprocessed'] == None:
        unprocessed_id = _createLabel(service, user_id, needed_labels['unprocessed'])
        labels_dict['unprocessed'] = unprocessed_id

    if labels_dict['processed'] == None:
        processed_id = _createLabel(service, user_id, needed_labels['processed'])
        labels_dict['processed'] = processed_id

    return labels_dict


def _createLabel(service, user_id, label_name):
    label_obj = {
        'messageListVisibility': 'show',
        'name': label_name,
        'labelListVisibility': 'labelShow'
    }

    try:
        created_label = service.users().labels().create(userId=user_id, body=label_obj).execute()
    except Exception as error:
        exitWithError(error)

    print('{} Created label with name {}, and id {}'.format(getTime(), created_label['name'], created_label['id']))
    return created_label['id']


def _initFilter(service, user_id, label_id):
    try:
        response = service.users().settings().filters().list(userId=user_id).execute()
    except Exception as error:
        exitWithError(error)

    filters = response['filter']

    for filter in filters:
        if filter['criteria']['from'] == haro_email:
            return filter['id']

    return _createFilter(service, user_id, label_id)


def _createFilter(service, user_id, label_id):
    filter_obj = {
        'id': 'haro_filter',
        'criteria': {
            'from': haro_email,
        },
        'action': {
            'addLabelIds': label_id
        }
    }

    try:
        created_filter = service.users().settings().filters().create(userId=user_id, body=filter_obj).execute()
    except Exception as error:
        exitWithError(error)

    return created_filter['id']
