import datetime
import colors
import sys

def exitWithError(error):
    colors.printFail('[+] Error occurred: {}'.format(error))
    sys.exit(1)


def getTime():
    time = datetime.datetime.now().replace(microsecond=0)
    return '[' + str(time) + ']'
