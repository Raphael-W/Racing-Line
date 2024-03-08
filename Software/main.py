import pygame
import pygame.freetype
from spline import *
from pygameUIElements import *

pygame.init()
pygame.display.set_caption("Bézier Curve")
screen = pygame.display.set_mode((1280, 720))#, pygame.RESIZABLE)
clock = pygame.time.Clock()
screenWidth, screenHeight = screen.get_size()
running = True

trackWidth = 50
screenBorder = 5

track = Curve()

programColours = {"background": (20, 20, 20),
                  "curve": (128, 128, 128),
                  "controlPoint": (24, 150, 204),
                  "mainGrid": (30, 30, 30),
                  "innerGrid": (25, 25, 25)}

def testButtonPress():
    track.points = []

UILayer = Layer("UI", 0)
testButton = Button(UILayer, screen, pygame, "MonoFont.ttf", (1050, 600), (100, 50), "Clear",18, (100, 0, 0), testButtonPress)
testLabel = Label(UILayer, screen, pygame, "MonoFont.ttf", 50, (30, 30), "Racing Line Finder", (40, 174, 191))
testSlider = Slider(UILayer, screen, pygame, "MonoFont.ttf", 18, "Size", (200, 200, 200), (200, 0, 0), (100, 200), 1, 200, (0, 100), (0, 0), 50)

def drawGrid(frequency, lineWidth, lineColor):
    columns = math.ceil(screenWidth / frequency)
    rows = math.ceil(screenHeight / frequency)

    for line in range(columns):
        pygame.draw.line(screen, lineColor, (line * frequency, 0), (line * frequency, screenHeight), lineWidth)

    for line in range(rows):
        pygame.draw.line(screen, lineColor, (0, line * frequency), (screenWidth, line * frequency), lineWidth)

def gradient(coords1, coords2):
    return -(coords2[1] - coords1[1]) / (coords2[0] - coords1[0])


while running:
    screenWidth, screenHeight = screen.get_size()
    mousePosX = pygame.mouse.get_pos()[0]
    mousePosY = pygame.mouse.get_pos()[1]

    screen.fill(programColours["background"])

    drawGrid(50, 2, programColours["mainGrid"])
    drawGrid(10, 1, programColours["innerGrid"])

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0] and (track.mouseHovering is None) and (not UILayer.mouseOnLayer((mousePosX, mousePosY))):
            index = -1
            if len(track.points) >= 2:
                onLine, nearPointIndex = track.mouseOnCurve(mousePosX, mousePosY, 20)
                if onLine: index = nearPointIndex
            track.add(ControlPoint(mousePosX, mousePosY), index = index)

        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[2] and (track.mouseHovering is not None) and (not UILayer.mouseOnLayer((mousePosX, mousePosY))):
            track.remove(index = track.mouseHovering)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_LCTRL and not(pygame.key.get_mods() & pygame.KMOD_LSHIFT):
                track.undo()

            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_LCTRL and pygame.key.get_mods() & pygame.KMOD_LSHIFT:
                track.redo()

    track.update(mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame)
    track.draw(programColours, screen, pygame)

    testLabel.text = str(testSlider.value)
    UILayer.display(mousePosX, mousePosY)

    pygame.display.flip()
    clock.tick(120) #Refresh Rate

pygame.quit()
