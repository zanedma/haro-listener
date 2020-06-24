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
