import datetime
import colors
import base64
from bs4 import BeautifulSoup
import sys

def exitWithError(error):
    colors.printFail('[+] Error occurred: {}'.format(error))
    sys.exit(1)


def getTime():
    time = datetime.datetime.now().replace(microsecond=0)
    return '[' + str(time) + ']'


def set_params():
    try:
        args = open('args', 'r')
    except FileNotFoundError as error:
        exitWithError(error)
    
    # split the entire file by lines
    lines = args.read().splitlines()
    params = {}
    params['notification_email'] = lines[0]
    params['user_email'] = lines[1]
    # all lines after the user_email line should be link keys, combine them
    link_keys = ' '.join(lines[2:])
    # split the lines by comma separator to obtain a list
    params['link_keys'] = link_keys.split(', ')
    return params
