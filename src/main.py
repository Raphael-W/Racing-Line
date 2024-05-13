import json
from jsonschema import validate

import pygame
import pygame.gfxdraw
import pygame.freetype

from tkinter.filedialog import asksaveasfilename, askopenfilename
import tkinter as tk

import os
import sys

from pygameUIElements import *
from spline import *

if os.name == "nt":
    import ctypes

    appID = 'Raphael Wreford, Racing-Line-Finder' # Arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID) #Makes taskbar icon same as window icon (Sets app as "individual app", not linked to python)

pygame.init()
pygame.display.set_caption("Racing Line Finder")
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
clock = pygame.time.Clock()
screenWidth, screenHeight = screen.get_size()

running = True
closeCount = 0

pivotPos = None
offsetPosition = (0, 0)
screenBorder = 5

zoom = 1
zoomIncrement = 0.05
upperZoomLimit = 2.5
lowerZoomLimit = 0.1

userSettingScale = False
setScalePoint1 = None
setScalePoint2 = None
realDistanceTextInput = None

viewMode = "Track"

userSettingFinish = False
finishIndex = None
finishDir = None

trackRes = 20
mainTrack = Track(resolution = trackRes)

programColours = {"background": (20, 20, 20),
                  "curve": (128, 128, 128),
                  "controlPoint": (24, 150, 204),
                  "frontControlPoint": (204, 138, 24),
                  "mainGrid": (30, 30, 30),
                  "innerGrid": (25, 25, 25),
                  "white": (200, 200, 200),
                  "mainTrack": (100, 100, 100)}

executionDir = os.path.dirname(os.path.dirname(__file__))
directories = {"mainFont": "assets/MonoFont.ttf",
               "recentreButton": "assets/aim.png",
               "finishLine": "assets/flag.png",
               "scale": "assets/scale.png",
               "minus": "assets/minus.png",
               "plus": "assets/plus.png",
               "cross": "assets/cross.png",
               "arrow": "assets/arrow.png",
               "undo": "assets/undo.png",
               "redo": "assets/redo.png",
               "down": "assets/down.png",
               "trackSchema": "schemas/trackSchema.json",
               "silverstone": "assets/silverstoneReference.png"}

directories = {item: os.path.normpath(os.path.join(executionDir, directory)) for (item, directory) in directories.items()}
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN])

with open(directories["trackSchema"]) as trackSchema:
    trackFileSchema = json.load(trackSchema)

saveDirectory = None
saved = True
newCaption = None
lastCaption = None

mainFont = directories["mainFont"]

def setEditStatus(value):
    mainTrack.edit = value
    if not value:
        mainTrack.computeTrack()
        mainTrack.deKink()
    else:
        mainTrack.computeTrack()

def recentreFrame():
    global offsetPosition, zoom

    minX = minY = float('inf')
    maxX = maxY = float('-inf')

    if len(mainTrack.points) >= 1:
        for point in mainTrack.returnPointCoords():
            if point[0] > maxX:
                maxX = point[0]
            if point[0] < minX:
                minX = point[0]

            if point[1] > maxY:
                maxY = point[1]
            if point[1] < minY:
                minY = point[1]
    else:
        minX = maxX = minY = maxY = 0

    centreX = (maxX + minX) / 2
    centreY = (maxY + minY) / 2

    zoomPercentage = (max((maxX - minX) / screenWidth, (maxY - minY) / screenHeight) * 1.05) + 0.3
    zoom = 1 / zoomPercentage
    zoom = min(max(zoom, lowerZoomLimit), upperZoomLimit)
    if len(mainTrack.points) == 0:
        zoom = 1

    offsetPosition = ((((screenWidth / zoom) / 2) - centreX) * zoom, (((screenHeight / zoom) / 2) - centreY) * zoom)

def setScale():
    global userSettingScale, setScalePoint1, setScalePoint2

    userSettingScale = True
    setScalePoint1 = None
    setScalePoint2 = None

def completeScaling(text):
    global userSettingScale, saved
    try:
        actualDistance = float(text)
    except:
        actualDistance = None
        scalingErrorLabel.text = "Please enter a valid number"

    scaleBefore = mainTrack.scale

    if actualDistance is not None:
        if actualDistance == 0:
            scalingErrorLabel.text = "Please enter a number greater than 0"
        else:
            screenDistance = pointDistance(setScalePoint1, setScalePoint2)
            mainTrack.scale = actualDistance / screenDistance
            realDistanceTextInput.close()
            userSettingScale = False
            mainTrack.saved = False
            mainTrack.calculateLength()
            scalingErrorLabel.text = ""
            mainTrack.history.addAction("SET SCALE", [scaleBefore, mainTrack.scale])

def setFinish():
    global userSettingFinish, finishIndex, finishDir

    userSettingFinish = True
    finishIndex = None
    finishDir = None

def completeFinish():
    global userSettingFinish

    mainTrack.history.addAction("SET FINISH", [[mainTrack.finishIndex, mainTrack.finishDir], [finishIndex, finishDir]])

    mainTrack.finishIndex = finishIndex
    mainTrack.finishDir = finishDir

    userSettingFinish = False
    mainTrack.saved = False

def setViewMode(mode):
    global viewMode

    viewMode = mode

UILayer = Layer("UI", 0, screen, pygame, mainFont, directories)
trackLayer = Layer("Track", 1, screen, pygame, mainFont, directories)

mouseXLabel = Label(UILayer, 15, (100, 30), "NE", "", programColours["white"])
mouseYLabel = Label(UILayer, 15, (100, 50), "NE", "", programColours["white"])
scaleLabel = Label(UILayer, 15, (127, 70), "NE", "", programColours["white"])
fpsLabel = Label(UILayer, 15, (40, 30), "", "fps: 120", programColours["white"])

switchEndsSwitch = Switch(UILayer, (165, 155), "SE", 0.8, value = False)
switchEndsLabel = Label(UILayer, 15, (280, 153), "SE", "Switch front", programColours["white"])

snapPointsSwitch = Switch(UILayer, (165, 125), "SE", 0.8, value = False)
snapPointsLabel = Label(UILayer, 15, (209, 123), "SE", "Snap", programColours["white"])

editModeSwitch = Switch(UILayer, (165, 95), "SE", 0.8, value = True, action = lambda: setEditStatus(editModeSwitch.value))
editModeLabel = Label(UILayer, 15, (209, 93), "SE", "Edit", programColours["white"])

viewModeDropdown = Dropdown(UILayer, (225, 195), "SE", (150, 25), ["Track", "Skeleton", "Curve", "Spline Dots"], 0, action = setViewMode)
viewModeLabel = Label(UILayer, 15, (330, 190), "SE", "View Mode", (200, 200, 200))

trackWidthSlider = Slider(UILayer, 15, programColours["white"], programColours["controlPoint"], (224, 228), "SE", 1,
                          100, (20, 200), value = mainTrack.width, action = mainTrack.changeWidth,
                          finishedUpdatingAction = mainTrack.changeWidthComplete)
trackWidthLabel = Label(UILayer, 15, (295, 233), "SE", "Width", programColours["white"])

trackResSlider = Slider(UILayer, 15, programColours["white"], programColours["controlPoint"], (225, 263), "SE", 1, 100,
                        (10, 100), value = mainTrack.perSegRes, action = mainTrack.changeRes,
                        finishedUpdatingAction = mainTrack.changeResComplete)
TrackResLabel = Label(UILayer, 15, (330, 268), "SE", "Track Res", programColours["white"])

setFinishButton = Button(UILayer, (330, 355), "SE", (80, 60), "Set Finish", 10, (100, 100, 100), (0, -18),
                         action = setFinish)
startFinishImage = Image(UILayer, (setFinishButton.posX - 28, setFinishButton.posY - 10), "SE", directories["finishLine"], 1, colour = (30, 30, 30))

setScaleButton = Button(UILayer, (242.5, 355), "SE", (80, 60), "Set Scale", 10, (100, 100, 100), (0, -18),
                        action = setScale)
scaleImage = Image(UILayer, (setScaleButton.posX - 28, setScaleButton.posY - 10), "SE", directories["scale"], 1, colour = (30, 30, 30))

recentreButton = Button(UILayer, (155, 355), "SE", (80, 60), "Recentre", 10, (100, 100, 100), (0, -18),
                        action = recentreFrame)
recentreImage = Image(UILayer, (recentreButton.posX - 27, recentreButton.posY - 10), "SE", directories["recentreButton"], 1, colour = (30, 30, 30))

undoButton = Button(UILayer, (330, 95), "SE", (30, 30), "", 12, (100, 100, 100), action = mainTrack.undo)
undoIcon = Image(UILayer, (undoButton.posX - 2, undoButton.posY - 2), "SE", directories["undo"], 0.8, colour = programColours["white"])

redoButton = Button(UILayer, (295, 95), "SE", (30, 30), "", 12, (100, 100, 100), action = mainTrack.redo)
redoIcon = Image(UILayer, (redoButton.posX - 2, redoButton.posY - 2), "SE", directories["redo"], 0.8, colour = programColours["white"])

configAccordion = Accordion(UILayer, (50, 50), "SE", (305, 455), "Untitled Track", [snapPointsSwitch, snapPointsLabel, switchEndsSwitch, switchEndsLabel, editModeSwitch, editModeLabel, trackWidthSlider, trackWidthLabel, trackResSlider, TrackResLabel, viewModeDropdown, viewModeLabel, setFinishButton, startFinishImage, setScaleButton, scaleImage, recentreButton, recentreImage, undoButton, undoIcon, redoButton, redoIcon], layerIndex = 0)

trackScaleLabel = Label(UILayer, 15, (180, 30), "S", "", programColours["white"])
scalingErrorLabel = Label(UILayer, 12, (20, 60), "S", "", (227, 65, 50))

finishIcon = Image(trackLayer, (0, 0), "", directories["finishLine"], 1, colour = (programColours["white"]), show = False)
finishDirIcon = Image(trackLayer, (0, 0), "", directories["arrow"], 1, colour = (programColours["white"]), show = False)

def drawGrid(offset, frequency, lineWidth, lineColor):
    columns = math.ceil(screenWidth/ frequency)
    rows = math.ceil(screenHeight/ frequency)

    startCol = int(-offset[0] // frequency)
    endCol = startCol + columns
    startRow = int(-offset[1] // frequency)
    endRow = startRow + rows

    for line in range(startCol, endCol + 1):
        x = line * frequency + offset[0]
        pygame.draw.line(screen, lineColor, (x, 0), (x, screenHeight), lineWidth)

    for line in range(startRow, endRow + 1):
        y = line * frequency + offset[1]
        pygame.draw.line(screen, lineColor, (0, y), (screenWidth, y), lineWidth)

def saveTrack(saveNewDirectory = False):
    global saveDirectory, mainTrack
    def closeError(sender):
        sender.close()

    points = mainTrack.returnPointCoords()
    properties = {"width": mainTrack.width,
                  "trackRes": mainTrack.perSegRes,
                  "closed": mainTrack.closed,
                  "switchEnds": switchEndsSwitch.value,
                  "snap": snapPointsSwitch.value,
                  "scale": mainTrack.scale,
                  "finishIndex": mainTrack.finishIndex,
                  "finishDir": mainTrack.finishDir}

    trackData = {"points": points,
             "properties": properties}

    def getFileName():
        root = tk.Tk()
        root.wm_attributes('-topmost', 1)
        root.withdraw()
        fileSelected = asksaveasfilename(title = "Save Track", initialfile = 'Untitled.track', defaultextension = ".track", filetypes = [("Track Files", "*.track")])
        root.destroy()
        return fileSelected


    validFile = True
    if saveDirectory is None or saveNewDirectory:
        tempDirectory = getFileName()
        if tempDirectory != '':
            validFile = os.path.isdir(os.path.dirname(tempDirectory))
        else:
            validFile = False
    else:
        tempDirectory = saveDirectory

    if validFile:
        try:
            with open(tempDirectory, "w") as outputFile:
                json.dump(trackData, outputFile, indent=4)
                pygame.display.set_caption(os.path.splitext(os.path.basename(tempDirectory))[0] + " - " + tempDirectory)
                saveDirectory = tempDirectory
                mainTrack.saved = True

        except Exception as error:
            Message(UILayer, "Can't Save", str(error), "OK", closeError, "grey")
            saveDirectory = None
            mainTrack.saved = False

    elif not validFile and tempDirectory != '':
        Message(UILayer, "Can't Save", "Please select a valid directory", "OK", closeError, "grey")
        saveDirectory = None
        mainTrack.saved = False

def openTrack(tempDirectory = None):
    global saveDirectory
    def validateTrackFile(directory):
        error = None
        try:
            with open(directory) as loadFile:
                try:
                    trackData = json.load(loadFile)
                    validate(instance = trackData, schema = trackFileSchema)
                except:
                    error = "Invalid"

        except Exception as error:
            error = error

        return error

    def loadTrack(directory):
        global saveDirectory

        validFile = validateTrackFile(directory)
        if validFile is None:
            with open(directory) as loadFile:
                trackData = json.load(loadFile)

                pointCoords = trackData["points"]
                mainTrack.loadTrackPoints(pointCoords)

                trackProperties = trackData["properties"]

                trackWidthSlider.updateValue(trackProperties["width"], update = False)
                mainTrack.width = trackProperties["width"]

                trackResSlider.updateValue(trackProperties["trackRes"], update = False)
                mainTrack.perSegRes = trackProperties["trackRes"]

                switchEndsSwitch.value = trackProperties["switchEnds"]
                snapPointsSwitch.value = trackProperties["snap"]
                mainTrack.scale = trackProperties["scale"]
                mainTrack.finishIndex = trackProperties["finishIndex"]
                mainTrack.finishDir = trackProperties["finishDir"]
                mainTrack.updateCloseStatus(trackProperties["closed"], update = False)

                mainTrack.computeTrack()

                saveDirectory = directory
                recentreFrame()

                mainTrack.saved = True

        elif validFile == "Invalid":
            Message(UILayer, "Invalid File", "Please select a valid file", "OK", closeError, "grey")
        else:
            Message(UILayer, "Can't Open", str(validFile), "OK", closeError, "grey")

    def getFileName():
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        fileSelected = askopenfilename(title = "Open Track", defaultextension = ".track", filetypes = [("Track Files", "*.track")])
        root.destroy()
        return fileSelected

    def closeError(sender):
        sender.close()

    def saveTrackFirst(sender):
        global saveDirectory
        sender.close()
        saveTrack()
        loadTrack(tempDirectory)

    def discardTrack(sender):
        global saveDirectory
        sender.close()
        loadTrack(tempDirectory)

    if tempDirectory is None:
        tempDirectory = getFileName()

    validDir = os.path.isfile(tempDirectory)
    if not validDir:
        Message(UILayer, "Invalid File", "Please select a valid file", "OK", closeError, "grey")

    if tempDirectory != '' and mainTrack.saved == False and validDir:
        Message(UILayer, "Sure?", "You currently have an unsaved file open", "Save", saveTrackFirst, "grey","Discard", discardTrack, "red")
    else:
        loadTrack(tempDirectory)

def newTrack():
    global saveDirectory

    def saveTrackFirst(sender):
        global saveDirectory

        sender.close()
        saveTrack()
        mainTrack.clear()
        recentreFrame()

        saveDirectory = None
    def discardTrack(sender):
        global saveDirectory

        sender.close()
        mainTrack.clear()
        recentreFrame()

        mainTrack.saved = True
        saveDirectory = None

    if not mainTrack.saved:
        Message(UILayer, "Sure?", "You currently have an unsaved file open", "Save", saveTrackFirst, "grey", "Discard", discardTrack, "red")

    elif saveDirectory is not None:
        saveTrack()
        mainTrack.clear()
        recentreFrame()

        mainTrack.saved = True
        saveDirectory = None

    else:
        recentreFrame()

def closeTrack():
    global closeCount
    def closeError(sender):
        global closeCount

        sender.close()
        closeCount = 0

    def saveTrackFirst():
        global running

        saveTrack()
        running = False

    def discardTrack(sender):
        global running

        running = False

    if closeCount == 0:
        unsavedTrackError = Message(UILayer, "Sure?", "You currently have an unsaved file open", "Save", saveTrackFirst, "grey", "Discard", discardTrack, "red", xAction = lambda: closeError(unsavedTrackError))
    closeCount += 1

saveButton = Button(UILayer, (330, 442.5), "SE", (123.75, 30), "Save", 12, (100, 100, 100), action = saveTrack)
saveAsButton = Button(UILayer, (198.75, 442.5), "SE", (123.75, 30), "Save As", 12, (100, 100, 100),
                      action = lambda: saveTrack(saveNewDirectory = True))
openTrackButton = Button(UILayer, (330, 405), "SE", (123.75, 30), "Open", 12, (100, 100, 100), action = openTrack)
newTrackButton = Button(UILayer, (198.75, 405), "SE", (123.75, 30), "New", 12, (100, 100, 100), action = newTrack)

configAccordion.elements += [saveButton, saveAsButton, openTrackButton, newTrackButton]

if len(sys.argv) > 1:
    openTrack(sys.argv[1])

recentreFrame()

while running:
    screenWidth, screenHeight = screen.get_size()
    mousePosX = pygame.mouse.get_pos()[0]
    mousePosY = pygame.mouse.get_pos()[1]

    screen.fill(programColours["background"])

    if pygame.mouse.get_pressed()[1]:
        if pivotPos is not None:
            offsetPosition = (mousePosX - pivotPos[0], mousePosY - pivotPos[1])
    else:
        pivotPos = None

    for event in pygame.event.get():
        #Handling QUIT event
        if event.type == pygame.QUIT:
            if not saved:
                closeTrack()

            if saved or closeCount > 1:
                running = False

        #Adding control point
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0] and (mainTrack.mouseHovering is None) and (not UILayer.mouseOnLayer((mousePosX, mousePosY))) and not (userSettingScale or userSettingFinish):
            index = -1
            if switchEndsSwitch.value:
                index = 0

            validPlacement = True
            onLine = False
            if len(mainTrack.points) >= 2:
                onLine, nearPointSegment, nearestPoint, nearPointIndex = mainTrack.pointOnCurve((mousePosX - offsetPosition[0]) / zoom, (mousePosY - offsetPosition[1]) / zoom, 20)
                if onLine:
                    index = nearPointSegment

            validPlacement = (not mainTrack.closed or onLine) and mainTrack.edit
            if validPlacement:
                mainTrack.add(ControlPoint((mousePosX - offsetPosition[0]) / zoom, (mousePosY - offsetPosition[1]) / zoom), index = index, userPerformed = True)

        #Removing control point
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[2] and (mainTrack.mouseHovering is not None) and (not UILayer.mouseOnLayer((mousePosX, mousePosY))) and not (userSettingScale or userSettingFinish):
            index = mainTrack.mouseHovering
            if not(mainTrack.closed and ((index == 0) or (index == len(mainTrack.points) - 1))) and mainTrack.edit:
                mainTrack.remove(index = index, userPerformed = True)

        #Set offset pivot
        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[1]:
            pivotPos = (mousePosX - offsetPosition[0], mousePosY - offsetPosition[1])

        #Set offset pivot
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                if zoom < upperZoomLimit:
                    beforeZoom = zoom
                    zoom *= 1 + zoomIncrement

                    if zoom > upperZoomLimit:
                        zoom = upperZoomLimit

                    zoomDifference = (zoom/beforeZoom) - 1
                    offsetPosition = (int(offsetPosition[0] - (mousePosX - offsetPosition[0]) * zoomDifference), int(offsetPosition[1] - (mousePosY - offsetPosition[1]) * zoomDifference))

            elif event.y < 0:
                if zoom > lowerZoomLimit:
                    beforeZoom = zoom
                    zoom *= 1 - zoomIncrement

                    if zoom < lowerZoomLimit:
                        zoom = lowerZoomLimit

                    zoomDifference = (beforeZoom/zoom) - 1
                    offsetPosition = (int(offsetPosition[0] + (mousePosX - offsetPosition[0]) * zoomDifference), int(offsetPosition[1] + (mousePosY - offsetPosition[1]) * zoomDifference))

        #Handling key presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_LCTRL and not(pygame.key.get_mods() & pygame.KMOD_LSHIFT) and mainTrack.edit:
                mainTrack.undo()

            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_LCTRL and pygame.key.get_mods() & pygame.KMOD_LSHIFT and mainTrack.edit:
                mainTrack.redo()

            if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_LCTRL:
                saveTrack()

            if event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_LCTRL:
                openTrack()

            if event.key == pygame.K_n and pygame.key.get_mods() & pygame.KMOD_LCTRL:
                newTrack()

        #Logic for setting scale
        if userSettingScale:
            if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0] and (not UILayer.mouseOnLayer((mousePosX, mousePosY))):
                if setScalePoint1 is None:
                    setScalePoint1 = ((mousePosX - offsetPosition[0]) / zoom, (mousePosY - offsetPosition[1]) / zoom)
                elif setScalePoint2 is None:
                    setScalePoint2 = ((mousePosX - offsetPosition[0]) / zoom, (mousePosY - offsetPosition[1]) / zoom)

                    realDistanceTextInput = TextInput(UILayer, (20, 120), "S", (180, 50), 15, "Real Distance (m)", "","m", ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '.'], enterAction = completeScaling)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if realDistanceTextInput is not None:
                        realDistanceTextInput.close()
                    userSettingScale = False

                if realDistanceTextInput is not None:
                    realDistanceTextInput.typeLetter(event)

        #Logic for setting finish
        if userSettingFinish:
            if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0] and (not UILayer.mouseOnLayer((mousePosX, mousePosY))):
                if finishIndex is None:
                    finishIndex = ((mousePosX - offsetPosition[0]) / zoom, (mousePosY - offsetPosition[1]) / zoom)
                    onLine, nearPointSegment, nearestPointCoords, nearestPoint = mainTrack.pointOnCurve(finishIndex[0], finishIndex[1], (mainTrack.width / 2))
                    if onLine:
                        finishIndex = nearestPoint / mainTrack.perSegRes
                    else:
                        finishIndex = None

                elif finishIndex is not None:
                    completeFinish()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    userSettingFinish = False

    drawGrid(offsetPosition, 50 * zoom, 2, programColours["mainGrid"])
    drawGrid(offsetPosition, 10 * zoom, 1, programColours["innerGrid"])

    screenRect = pygame.Rect((0, 0), (screenWidth + 15, screenHeight + 15))

    if not(userSettingScale or userSettingFinish):
        mainTrack.update((mousePosX - offsetPosition[0]) / zoom, (mousePosY - offsetPosition[1]) / zoom, zoom, screenWidth, screenHeight, screenBorder, pygame, offsetPosition, snapPointsSwitch.value, screenRect)
    mainTrack.draw(programColours, screen, pygame, offsetPosition, zoom, switchEndsSwitch.value, screenRect, viewMode)

    if userSettingScale:
        transparentSurface = pygame.Surface((screenWidth, screenHeight), pygame.SRCALPHA)
        pygame.draw.rect(transparentSurface, (50, 50, 50, 100), (0, 0, screenWidth, screenHeight))
        screen.blit(transparentSurface, (0, 0))

        if setScalePoint1 is not None:
            lineStart = ((setScalePoint1[0] * zoom) + offsetPosition[0], (setScalePoint1[1] * zoom) + offsetPosition[1])
            if setScalePoint2 is None:
                lineEnd = (mousePosX, mousePosY)
            else:
                lineEnd = ((setScalePoint2[0] * zoom) + offsetPosition[0], (setScalePoint2[1] * zoom) + offsetPosition[1])

            endStopsStart = calculateSide([lineStart, lineEnd], 0, 20)
            endStopsEnd = calculateSide([lineStart, lineEnd], 0, -20)

            lineStart_EndStop = [calculateSide([lineStart, lineEnd], 0, 20),
                                calculateSide([lineStart, lineEnd], 0, -20)]

            lineEnd_EndStop = [calculateSide([lineStart, lineEnd], 1, 20),
                                calculateSide([lineStart, lineEnd], 1, -20)]

            pygame.draw.line(screen, (200, 200, 200), lineStart, lineEnd, 5)
            pygame.draw.line(screen, (200, 200, 200), lineStart_EndStop[0], lineStart_EndStop[1], 5)
            pygame.draw.line(screen, (200, 200, 200), lineEnd_EndStop[0], lineEnd_EndStop[1], 5)

    if userSettingFinish:
        transparentSurface = pygame.Surface((screenWidth, screenHeight), pygame.SRCALPHA)
        pygame.draw.rect(transparentSurface, (50, 50, 50, 100), (0, 0, screenWidth, screenHeight))
        screen.blit(transparentSurface, (0, 0))

        if finishIndex is not None:
            if angle(offsetPoints((mousePosX, mousePosY), offsetPosition, zoom, True, True),
                     mainTrack.splinePoints[int(finishIndex * mainTrack.perSegRes)],
                     extendPointsBack(mainTrack.splinePoints)[int(finishIndex * mainTrack.perSegRes) + 1]) < 90:
                finishDir = True
            else:
                finishDir = False

    else:
        finishIndex = mainTrack.finishIndex
        finishDir = mainTrack.finishDir

    if finishIndex is not None:
        if ((len(mainTrack.points) - 1) < finishIndex) or (finishIndex < 0):
            mainTrack.finishIndex = None
            mainTrack.finishDir = None

            finishIndex = None
            finishDir = None

    if finishIndex is not None:
        finishIcon.show = True
        finishDirIcon.show = True
    else:
        finishIcon.show = False
        finishDirIcon.show = False

    if finishIndex is not None:
        finishPointCoords = (mainTrack.splinePoints[int(finishIndex * mainTrack.perSegRes)])
        finishPointNeighbourCoords = (extendPointsBack(mainTrack.splinePoints)[int(finishIndex * mainTrack.perSegRes) + 1])
        finishPointNeighboursDistance = pointDistance(finishPointNeighbourCoords, finishPointCoords)

        arrowEndExtX = ((finishPointNeighbourCoords[0] - finishPointCoords[0]) / finishPointNeighboursDistance) / zoom
        arrowEndExtY = ((finishPointNeighbourCoords[1] - finishPointCoords[1]) / finishPointNeighboursDistance) / zoom
        arrowPos = (finishPointCoords[0] + (arrowEndExtX * 80 * finishDir) - (arrowEndExtX * 40), finishPointCoords[1] + (arrowEndExtY * 80 * finishDir) - (arrowEndExtY * 40))

        trackAngle = 0 + math.degrees(math.atan2(finishPointCoords[0] - finishPointNeighbourCoords[0], (finishPointCoords[1] - finishPointNeighbourCoords[1]))) - 90

        finishIconSize = finishIcon.getSize()
        finishDirIconSize = finishDirIcon.getSize()

        finishIcon.posX, finishIcon.posY = (finishPointCoords[0] - (finishIconSize[0] / 2), finishPointCoords[1] - (finishIconSize[1] / 2))
        finishDirIcon.posX, finishDirIcon.posY = (arrowPos[0] - (finishDirIconSize[0] / 2), arrowPos[1] - (finishDirIconSize[1] / 2))
        finishDirIcon.angle = trackAngle + (finishDir * 180)

    if len(mainTrack.points) >= 2:
        editModeSwitch.disabled = False
    else:
        editModeSwitch.disabled = True

    if not mainTrack.edit:
        trackWidthSlider.disabled = True
        trackResSlider.disabled = True
        switchEndsSwitch.disabled = True
        snapPointsSwitch.disabled = True

    else:
        trackWidthSlider.disabled = False
        trackResSlider.disabled = False
        switchEndsSwitch.disabled = False
        snapPointsSwitch.disabled = False

    saved = mainTrack.saved
    if saved:
        saveCharacter = ""
    else:
        saveCharacter = "*"

    if saveDirectory is None:
        newCaption = "Untitled Track" + saveCharacter
        configAccordion.titleText = "Untitled Track" + saveCharacter
    else:
        newCaption = str(os.path.splitext(os.path.basename(saveDirectory))[0] + saveCharacter + " - " + saveDirectory)
        configAccordion.titleText = str(os.path.splitext(os.path.basename(saveDirectory))[0] + saveCharacter)

    if lastCaption != newCaption:
        pygame.display.set_caption(newCaption)

    lastCaption = newCaption
    mouseXLabel.text = ("x: " + str(int(((mousePosX * 1) - offsetPosition[0]) / zoom)))
    mouseYLabel.text = ("y: " + str(int(((mousePosY * 1) - offsetPosition[1]) / zoom)))
    scaleLabel.text = ("view: " + str(int(zoom * 100)) + "%")
    fpsLabel.text = ("fps: " + str(int(clock.get_fps())))

    if len(mainTrack.history.undoStack) == 0:
        undoButton.disabled = True
        undoIcon.colour = (90, 90, 90)
    else:
        undoButton.disabled = False
        undoIcon.colour = programColours["white"]

    if len(mainTrack.history.redoStack) == 0:
        redoButton.disabled = True
        redoIcon.colour = (90, 90, 90)
    else:
        redoButton.disabled = False
        redoIcon.colour = programColours["white"]

    if mainTrack.scale is not None:
        trackScaleReduced = int((mainTrack.scale * 150) / zoom)

        if mainTrack.length > 1000:
            lengthText = "length: " + str(int(mainTrack.length) / 1000) + "km"
        else:
            lengthText = "length: " + str(int(mainTrack.length)) + "m"

        trackScaleLabel.text = str(trackScaleReduced) + "m  | " + lengthText
        scaleFont = pygame.freetype.Font(mainFont, 15)

        pygame.draw.line(screen, (200, 200, 200), (20, screenHeight - 35), (20, screenHeight - 20), 2)
        pygame.draw.line(screen, (200, 200, 200), (20, screenHeight - 20), (170, screenHeight - 20), 2)
        pygame.draw.line(screen, (200, 200, 200), (170, screenHeight - 35), (170, screenHeight - 20), 2)
    else:
        trackScaleLabel.text = ""

    trackLayer.display(screenWidth, screenHeight, offsetPosition, zoom)
    UILayer.display(screenWidth, screenHeight)

    pygame.display.flip()
    clock.tick(120) #Refresh Rate

pygame.quit()
