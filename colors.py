HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

def printHeader(message):
    print('{}{}{}'.format(HEADER, message, ENDC))

def printBlue(message):
    print('{}{}{}'.format(OKBLUE, message, ENDC))

def printGreen(message):
    print('{}{}{}'.format(OKGREEN, message, ENDC))

def printWarning(message):
    print('{}{}{}'.format(WARNING, message, ENDC))

def printFail(message):
    print('{}{}{}'.format(FAIL, message, ENDC))

def printBold(message):
    print('{}{}{}'.format(BOLD, message, ENDC))

def printUnderline(message):
    print('{}{}{}'.format(UNDERLINE, message, ENDC))
