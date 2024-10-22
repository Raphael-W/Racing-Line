import os
import requests
from datetime import datetime
import threading
import time

def getModifiedDate(fileDir):
    try:
         modifiedDate = os.path.getmtime(fileDir)
         timezoneOffset = time.localtime().tm_gmtoff
         return modifiedDate - timezoneOffset
    except:
        return -1
def getDataFromLatestCommit():
    url = "https://api.github.com/repos/Raphael-W/Racing-Line/branches/master"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            lastCommitDate = data['commit']['commit']['committer']['date']
            lastCommmitSHA = data['commit']['commit']['tree']['sha']

            dateTimeObject = datetime.strptime(lastCommitDate, "%Y-%m-%dT%H:%M:%SZ")
            unixTimestamp = float(dateTimeObject.timestamp())
            return unixTimestamp, lastCommmitSHA
        else:
            return -1, -1

    except:
        return -1, -1

def isUpdateRequired(fileCheck, updateAction):
    def mainCheck():
        modifiedDate = getModifiedDate(fileCheck)
        latestCommitDate, latestCommitSHA = getDataFromLatestCommit()

        if not ((modifiedDate < 0) or (latestCommitDate < 0)) and (modifiedDate < latestCommitDate):
            updateAction(latestCommitSHA)

    mainThread = threading.Thread(target = mainCheck)
    mainThread.start()
