import datetime
import colors
import base64
from bs4 import BeautifulSoup
import sys

def exitWithError(error):
    """ Exit with formatted error message and exit code 1

    @param error String: Error message/reason for exit
    """
    colors.printFail('[+] Error occurred: {}'.format(error))
    sys.exit(1)


def getTime():
    """Get the current time and format it into a String

    @return String current time
    """
    time = datetime.datetime.now().replace(microsecond=0)
    return '[' + str(time) + ']'


def set_params():
    """set the params from the necessary args file

    @return Dict: parameter key/value pairs
    """
    try:
        args = open('args', 'r')
    except FileNotFoundError as error:
        exitWithError(error)
    
    # split the entire file by lines
    lines = args.read().splitlines()
    params = {}
    params['notification_emails'] = lines[0].split(', ')
    params['user_email'] = lines[1]
    # all lines after the user_email line should be link keys, combine them
    link_keys = ' '.join(lines[2:])
    # split the lines by comma separator to obtain a list
    params['link_keys'] = link_keys.split(', ')
    return params
