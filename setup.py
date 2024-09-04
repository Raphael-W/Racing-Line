import os
from win32com.client import Dispatch

#Installing Requirements
os.system("pip install -r requirements.txt")

#Creating a shortcut to main.pyw
executionDir = os.path.dirname(__file__)
mainScriptPath = os.path.normpath(os.path.join(executionDir, "src/main.pyw"))
shortcutPath = os.path.join(executionDir, "Racing Line.lnk")
iconPath = os.path.join(executionDir, "assets/icons/logo.ico")

shell = Dispatch('WScript.Shell')
shortcut = shell.CreateShortCut(shortcutPath)
shortcut.Targetpath = mainScriptPath
shortcut.IconLocation = iconPath
shortcut.save()
