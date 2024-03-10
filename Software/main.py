import pygame
import pygame.freetype
from spline import *
from pygameUIElements import *

pygame.init()
pygame.display.set_caption("Racing Line Finder")
screen = pygame.display.set_mode((1280, 720))#, pygame.RESIZABLE)
clock = pygame.time.Clock()
screenWidth, screenHeight = screen.get_size()
running = True

pivotPos = None
offsetPosition = (0, 0)

trackWidth = 50
screenBorder = 5

mainTrack = Track()

programColours = {"background": (20, 20, 20),
                  "curve": (128, 128, 128),
                  "controlPoint": (24, 150, 204),
                  "mainGrid": (30, 30, 30),
                  "innerGrid": (25, 25, 25)}

def testButtonPress():
    mainTrack.points = []

UILayer = Layer("UI", 0)
mouseCoordsX = Label(UILayer, screen, pygame, "MonoFont.ttf", 15, (1150, 650), "", (200, 200, 200))
mouseCoordsY = Label(UILayer, screen, pygame, "MonoFont.ttf", 15, (1150, 670), "", (200, 200, 200))

magneticSwitch = Switch(UILayer, screen, pygame, "MonoFont.ttf", (200, 200, 200), (1180, 600), 0.8, value = False)
magneticLabel = Label(UILayer, screen, pygame, "MonoFont.ttf", 15, (1120, 604), "Snap:", (200, 200, 200))

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
            if len(mainTrack.points) >= 2:
                onLine, nearPointIndex = mainTrack.mouseOnCurve(mousePosX - offsetPosition[0], mousePosY - offsetPosition[1], 20)
                if onLine: index = nearPointIndex
            mainTrack.add(ControlPoint(mousePosX - offsetPosition[0], mousePosY - offsetPosition[1]), index = index)

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
    mainTrack.draw(programColours, screen, pygame, offsetPosition)

    mouseCoordsX.text = ("x: " + str(mousePosX - offsetPosition[0]))
    mouseCoordsY.text = ("y: " + str(mousePosY - offsetPosition[1]))
    UILayer.display()


    pygame.display.flip()
    clock.tick(60) #Refresh Rate

pygame.quit()
