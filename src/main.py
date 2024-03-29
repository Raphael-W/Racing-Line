import json

import pygame
import pygame.gfxdraw
import pygame.freetype

from pygameUIElements import *
from spline import *

import ctypes

appID = 'Raphael Wreford, Racing-Line-Finder' # Arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID) #Makes taskbar icon same as window icon (Sets app as "individual app" not linked to python)

pygame.init()
pygame.display.set_caption("Racing Line Finder")
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
clock = pygame.time.Clock()
screenWidth, screenHeight = screen.get_size()
running = True

pivotPos = None
offsetPosition = (0, 0)
screenBorder = 5

mainTrack = Track()

programColours = {"background": (20, 20, 20),
                  "curve": (128, 128, 128),
                  "controlPoint": (24, 150, 204),
                  "frontControlPoint": (204, 138, 24),
                  "mainGrid": (30, 30, 30),
                  "innerGrid": (25, 25, 25),
                  "white": (200, 200, 200),
                  "mainTrack": (100, 100, 100)}

directories = {"mainFont": "../assets/MonoFont.ttf",
               "recentre": "../assets/aim.png",
               "finishLine": "../assets/flag.png",
               "scale": "../assets/scale.png",
               "minus": "../assets/minus.png",
               "plus": "../assets/plus.png"}

mainFont = directories["mainFont"]

UILayer = Layer("UI", 0, screen, pygame, mainFont, directories)

mouseCoordsX = Label(UILayer, 15, (100, 50), "NE", "", programColours["white"])
mouseCoordsY = Label(UILayer, 15, (100, 30), "NE", "", programColours["white"])

snapPoints = Switch(UILayer, programColours["white"], (140, 100), "SE", 0.8, value = False)
snapPointsLabel = Label(UILayer, 15, (193, 98), "SE", "Snap", programColours["white"])

switchEnds = Switch(UILayer, programColours["white"], (140, 130), "SE", 0.8, value = False)
switchEndsLabel = Label(UILayer, 15, (255, 128), "SE", "Switch front", programColours["white"])

trackWidth = Slider(UILayer, 15, programColours["white"], programColours["controlPoint"], (200, 173), "SE", 1, 100, (20, 200), action = lambda: mainTrack.changeWidth(trackWidth.value), value = mainTrack.width)
trackWidthLabel = Label(UILayer, 15, (270, 178), "SE", "Width", programColours["white"])

trackRes = Slider(UILayer, 15, programColours["white"], programColours["controlPoint"], (200, 208), "SE", 1, 100, (10, 100), action = lambda: mainTrack.changeRes(trackRes.value), value = mainTrack.perSegRes)
TrackResLabel = Label(UILayer, 15, (305, 213), "SE", "Track Res", programColours["white"])

setFinish = Button(UILayer, (305, 300), "SE", (80, 60), "Set Finish", 10, (100, 100, 100), (0, -18), action = None)
startFinishImage = Image(UILayer, (setFinish.posX - 28, setFinish.posY - 10), "SE", directories["finishLine"], 1, (30, 30, 30))

setScale = Button(UILayer, (217.5, 300), "SE", (80, 60), "Set Scale", 10, (100, 100, 100), (0, -18), action = None)
scaleImage = Image(UILayer, (setScale.posX - 28, setScale.posY - 10), "SE", directories["scale"], 1, (30, 30, 30))

recentre = Button(UILayer, (130, 300), "SE", (80, 60), "Recentre", 10, (100, 100, 100), (0, -18), action = None)
recentreImage = Image(UILayer, (recentre.posX - 27, recentre.posY - 10), "SE", directories["recentre"], 1, (30, 30, 30))

configAccordion = Accordion(UILayer, (330, 440), "SE", (305, 415), [snapPoints, snapPointsLabel, switchEnds, switchEndsLabel, trackWidth, trackWidthLabel, trackRes, TrackResLabel, setFinish, startFinishImage, setScale, scaleImage, recentre, recentreImage], layerIndex = 0)

def drawGrid(offset, frequency, lineWidth, lineColor):
    columns = math.ceil(screenWidth/ frequency)
    rows = math.ceil(screenHeight/ frequency)

    startCol = math.floor(-offset[0] / frequency)
    endCol = startCol + columns
    startRow = math.floor(-offset[1] / frequency)
    endRow = startRow + rows

    for line in range(startCol, endCol + 1):
        x = line * frequency + offset[0]
        pygame.draw.line(screen, lineColor, (x, 0), (x, screenHeight), lineWidth)

    for line in range(startRow, endRow + 1):
        y = line * frequency + offset[1]
        pygame.draw.line(screen, lineColor, (0, y), (screenWidth, y), lineWidth)

def saveTrack():
    points = mainTrack.saveTrackPoints()
    settings = {"width": mainTrack.width,
                "trackRes": mainTrack.perSegRes,
                "closed": mainTrack.closed,
                "switchEnds": switchEnds.value,
                "snap": snapPoints.value}

    trackData = {"points": points,
             "settings": settings}

    with open("testTrack.track", "w") as outputFile:
        json.dump(trackData, outputFile)

def loadTrack():
    with open("testTrack.track") as loadFile:
        trackData = json.load(loadFile)

    pointCoords = list(trackData["points"].values())
    mainTrack.loadTrackPoints(pointCoords)

    mainTrack.computeSpline()
    mainTrack.computeTrackEdges()

    trackSettings = trackData["settings"]
    trackWidth.updateValue(trackSettings["width"])
    trackRes.updateValue(trackSettings["trackRes"])
    mainTrack.updateCloseStatus(trackSettings["closed"], update = True)
    switchEnds.value = trackSettings["switchEnds"]
    snapPoints.value = trackSettings["snap"]


save = Button(UILayer, (305, 387.5), "SE", (123.75, 30), "Save", 12, (100, 100, 100), action = saveTrack)
saveAs = Button(UILayer, (173.75, 387.5), "SE", (123.75, 30), "Save As", 12, (100, 100, 100), action = saveTrack)
openTrack = Button(UILayer, (305, 350), "SE", (123.75, 30), "Open", 12, (100, 100, 100), action = loadTrack)
newTrack = Button(UILayer, (173.75, 350), "SE", (123.75, 30), "New", 12, (100, 100, 100), action = loadTrack)

configAccordion.elements += [save, saveAs, openTrack, newTrack]


while running:
    screenWidth, screenHeight = screen.get_size()
    mousePosX = pygame.mouse.get_pos()[0]
    mousePosY = pygame.mouse.get_pos()[1]

    screen.fill(programColours["background"])

    drawGrid(offsetPosition, 50, 2, programColours["mainGrid"])
    drawGrid(offsetPosition, 10, 1, programColours["innerGrid"])

    if pygame.mouse.get_pressed()[1]:
        if pivotPos is not None:
            offsetPosition = (mousePosX - pivotPos[0], mousePosY - pivotPos[1])
    else:
        pivotPos = None


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0] and (mainTrack.mouseHovering is None) and (not UILayer.mouseOnLayer((mousePosX, mousePosY))):
            index = -1
            if switchEnds.value:
                index = 0

            validPlacement = True
            onLine = False
            if len(mainTrack.points) >= 2:
                onLine, nearPointIndex = mainTrack.mouseOnCurve(mousePosX - offsetPosition[0], mousePosY - offsetPosition[1], 20)
                if onLine: index = nearPointIndex


            validPlacement = not mainTrack.closed or onLine
            if validPlacement: mainTrack.add(ControlPoint(mousePosX - offsetPosition[0], mousePosY - offsetPosition[1]), index = index)

        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[2] and (mainTrack.mouseHovering is not None) and (not UILayer.mouseOnLayer((mousePosX, mousePosY))):
            index = mainTrack.mouseHovering
            if not(mainTrack.closed and ((index == 0) or (index == len(mainTrack.points) - 1))):
                mainTrack.remove(index = index)

        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[1]:
            pivotPos = (mousePosX - offsetPosition[0], mousePosY - offsetPosition[1])

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_LCTRL and not(pygame.key.get_mods() & pygame.KMOD_LSHIFT):
                mainTrack.undo()

            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_LCTRL and pygame.key.get_mods() & pygame.KMOD_LSHIFT:
                mainTrack.redo()

    mainTrack.update(mousePosX - offsetPosition[0], mousePosY - offsetPosition[1], screenWidth, screenHeight, screenBorder, pygame, offsetPosition, snapPoints.value)
    mainTrack.draw(programColours, screen, pygame, offsetPosition, switchEnds.value)

    mouseCoordsX.text = ("x: " + str(mousePosX - offsetPosition[0]))
    mouseCoordsY.text = ("y: " + str(mousePosY - offsetPosition[1]))

    UILayer.display(screenWidth, screenHeight)

    pygame.display.flip()
    clock.tick(60) #Refresh Rate

pygame.quit()
