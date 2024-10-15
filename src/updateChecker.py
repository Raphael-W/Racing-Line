import os
import platform
import requests
from datetime import datetime
import threading

def getCreationDate(fileDir):
    try:
        if platform.system() == 'Windows':
            return os.path.getctime(fileDir)
        else:
            stat = os.stat(fileDir)
            try:
                return stat.st_birthtime
            except:
                return stat.st_mtime
    except:
        return -1
def getDateOfLatestCommit():
    url = "https://api.github.com/repos/Raphael-W/Racing-Line/branches/master"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            lastCommitDate = data['commit']['commit']['committer']['date']

            dateTimeObject = datetime.strptime(lastCommitDate, "%Y-%m-%dT%H:%M:%SZ")
            unixTimestamp = float(dateTimeObject.timestamp())
            return unixTimestamp
        else:
            return -1

    except:
        return -1

def isUpdateRequired(fileCheck, updateAction):
    def mainCheck():
        creationDate = getCreationDate(fileCheck)
        latestCommitDate = getDateOfLatestCommit()

        if not ((creationDate < 0) or (latestCommitDate < 0)) and (creationDate < latestCommitDate):
            updateAction()

    mainThread = threading.Thread(target = mainCheck)
    mainThread.start()
