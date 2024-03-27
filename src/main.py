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

mainFont = "../assets/MonoFont.ttf"

UILayer = Layer("UI", 0, screen, pygame, mainFont)
trackLayer = Layer("Track", 1, screen, pygame, mainFont)

mouseCoordsX = Label(UILayer, 15, (100, 50), "NE", "", programColours["white"])
mouseCoordsY = Label(UILayer, 15, (100, 30), "NE", "", programColours["white"])

magneticSwitch = Switch(UILayer, programColours["white"], (120, 100), "SE", 0.8, value = False)
magneticLabel = Label(UILayer, 15, (163, 98), "SE", "Snap", programColours["white"])

switchFront = Switch(UILayer, programColours["white"], (120, 130), "SE", 0.8, value = False)
switchFrontLabel = Label(UILayer, 15, (235, 128), "SE", "Switch front", programColours["white"])

trackWidth = Slider(UILayer, 15, programColours["white"], programColours["controlPoint"], (180, 173), "SE", 1, 100, (20, 200), action = lambda: mainTrack.changeWidth(trackWidth.value), value = mainTrack.width)
trackWidthLabel = Label(UILayer, 15, (240, 178), "SE", "Width", programColours["white"])

trackRes = Slider(UILayer, 15, programColours["white"], programColours["controlPoint"], (180, 208), "SE", 1, 100, (10, 100), action = lambda: mainTrack.changeRes(trackRes.value), value = mainTrack.perSegRes)
changeTrackRes = Label(UILayer, 15, (275, 213), "SE", "Track Res", programColours["white"])

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
            if switchFront.value:
                index = 0

            validPlacement = True
            onLine = False
            if len(mainTrack.points) >= 2:
                onLine, nearPointIndex = mainTrack.mouseOnCurve(mousePosX - offsetPosition[0], mousePosY - offsetPosition[1], 20)
                if onLine: index = nearPointIndex


            validPlacement = not mainTrack.closed or onLine
            if validPlacement: mainTrack.add(ControlPoint(mousePosX - offsetPosition[0], mousePosY - offsetPosition[1]), index = index)

        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[2] and (mainTrack.mouseHovering is not None) and (not UILayer.mouseOnLayer((mousePosX, mousePosY))):
            mainTrack.remove(index = mainTrack.mouseHovering)

        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[1]:
            pivotPos = (mousePosX - offsetPosition[0], mousePosY - offsetPosition[1])

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_LCTRL and not(pygame.key.get_mods() & pygame.KMOD_LSHIFT):
                mainTrack.undo()

            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_LCTRL and pygame.key.get_mods() & pygame.KMOD_LSHIFT:
                mainTrack.redo()

    mainTrack.update(mousePosX - offsetPosition[0], mousePosY - offsetPosition[1], screenWidth, screenHeight, screenBorder, pygame, offsetPosition, magneticSwitch.value)
    mainTrack.draw(programColours, screen, pygame, offsetPosition, switchFront.value)

    mouseCoordsX.text = ("x: " + str(mousePosX - offsetPosition[0]))
    mouseCoordsY.text = ("y: " + str(mousePosY - offsetPosition[1]))

    UILayer.display(screenWidth, screenHeight)
    trackLayer.display(screenWidth, screenHeight, offsetPosition)

    pygame.display.flip()
    clock.tick(60) #Refresh Rate

pygame.quit()
