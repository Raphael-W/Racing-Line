import numpy as np
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
zoom = 1
trackWidth = 50

spline = Curve()

backgroundColor = (20, 20, 20)
curveColor = (128, 128, 128)
controlPointColor = (24, 150, 204)
gridColor = (30, 30, 30)

ft_font = pygame.freetype.Font("KodeMono-VariableFont_wght.ttf", 24)

def displaySpline():
    if len(spline.points) >= 2:
        zoomedSplinePoints = list(np.array(spline.splinePoints) * zoom)
        pygame.draw.lines(screen, curveColor, False, zoomedSplinePoints, int(2 * (zoom * 2)))
        #pygame.draw.lines(screen, curveColor, False, leftTrackEdge.splinePoints, int(2 * (zoom * 2)))
        #pygame.draw.lines(screen, curveColor, False, rightTrackEdge.splinePoints, int(2 * (zoom * 2)))

    for point in spline.points:
        zoomedX = point.posX * zoom
        zoomedY = point.posY * zoom
        pygame.draw.circle(screen, controlPointColor, (zoomedX, zoomedY), zoom * point.size)

def updateSpline():
    screenBorder = 5

    for pointIndex in range(len(spline.points)):
        point = spline.points[pointIndex]

        point.mouseHovering = ((point.posX + (point.size + 2) > mousePosX > point.posX - (point.size + 2)) and
                               (point.posY + (point.size + 2) > mousePosY > point.posY - (point.size + 2)))

        if point.mouseHovering:
            point.size = point.baseSize + 2
            if pygame.mouse.get_pressed()[0] and spline.pointSelected is None:
                point.pointSelected = True
                spline.pointSelected = pointIndex
                point.originalPos = (point.posX, point.posY)
        else:
            point.size = point.baseSize

        if not pygame.mouse.get_pressed()[0]:
            point.pointSelected = False
            spline.pointSelected = None

        if point.pointSelected:
            if screenBorder < mousePosX < screenWidth - screenBorder:
                point.posX = mousePosX

            if screenBorder < mousePosY < screenHeight - screenBorder:
                point.posY = mousePosY

    if spline.pointSelected  is not None:
        spline.computeSpline(perSegRes = 20, updatePoints = spline.pointSelected)

    if len(spline.points) >= 4:
        leftTrackEdge, rightTrackEdge = spline.computeTrackEdges(trackWidth)

        leftTrackEdge = Curve(leftTrackEdge)
        rightTrackEdge = Curve(rightTrackEdge)

        leftTrackEdge.computeSpline(perSegRes = 20)
        rightTrackEdge.computeSpline(perSegRes = 20)

        pygame.draw.lines(screen, curveColor, False, rightTrackEdge.splinePoints, 5)
        pygame.draw.lines(screen, curveColor, False, leftTrackEdge.splinePoints, 5)

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
    mousePosX = pygame.mouse.get_pos()[0] / zoom
    mousePosY = pygame.mouse.get_pos()[1] / zoom

    screen.fill(backgroundColor)
    drawGrid(50 * zoom, 2, gridColor)
    drawGrid(10 * zoom, 1, (25, 25, 25))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0] and (spline.pointHovering() is None):
            spline.add(ControlPoint(mousePosX, mousePosY))

        if event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[2] and (spline.pointHovering()):
            spline.removeSpecific(spline.pointHovering())

        if event.type == pygame.KEYDOWN:
            if pygame.key.get_pressed()[pygame.K_BACKSPACE]:
                spline.removeLast()

            if pygame.key.get_pressed()[pygame.K_UP]:
                zoom *= 1.1

            if pygame.key.get_pressed()[pygame.K_DOWN]:
                zoom /= 1.1

    updateSpline()
    displaySpline()

    controlPoints = spline.returnPointCoords()

    for seg in range(1, len(controlPoints) - 1):
        grad = gradient(controlPoints[seg - 1], controlPoints[seg + 1])
        #grad = cardinal_spline(controlPoints, ((seg - 1) * 20) / (len(controlPoints) * 20), True)

        if grad != 0:
            perpGrad = ((1 / grad) * -1)
        else:
            perpGrad = 0

        perpGrad = grad
        ft_font.render_to(screen, (controlPoints[seg][0], controlPoints[seg][1] - 20), "{:.2f}".format(perpGrad),
                          (250, 250, 250))
        yIntercept = controlPoints[seg][1] - (perpGrad * controlPoints[seg][0])

        xR = controlPoints[seg][0] + (50 / math.sqrt(1 + (perpGrad ** 2)))
        yR = (perpGrad * xR) + yIntercept

        xL = controlPoints[seg][0] - (50 / math.sqrt(1 + (perpGrad ** 2)))
        yL = (perpGrad * xL) + yIntercept

        if False:
            innerCoords = (xR, yR)
            outerCoords = (xL, yL)

        else:
            innerCoords = (xL, yL)
            outerCoords = (xR, yR)

        pygame.draw.line(screen, curveColor, innerCoords, outerCoords, 5)
        pygame.draw.circle(screen, curveColor, innerCoords, 10)

    pygame.display.flip()
    clock.tick(120) #Refresh Rate

pygame.quit()
