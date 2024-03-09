import math
import numpy as np

#Calculates distance between 2 points
def pointDistance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    return math.sqrt(((y2 - y1) ** 2) + ((x1 - x2) ** 2))

#Returns a position on the curve given t and the control points
def calculateSpline(control_points, t, calcGrad = False):
    control_points = [control_points[1]] + control_points + [control_points[-2]]

    #Interpolate curve using Catmull Rom
    def interpolate(P0, P1, P2, P3, T):

        P0 = np.array(P0)
        P1 = np.array(P1)
        P2 = np.array(P2)
        P3 = np.array(P3)

        if calcGrad:
            return 0.5 * (((T * T) * ((3 * P3[0]) - (18 * P2[0]) + (18 * P1[0]) - (6 * P0[0]))) + (T * ((-2 * P3[0]) + (16 * P2[0]) - (20 * P1[0]) + (8 * P0[0]))) + (2 * P2[0]) - (2 * P0[0])) + T
        else:
            return (
                T * ((2 - T) * T - 1) * P0
                + (T * T * (3 * T - 5) + 2) * P1
                + T * ((4 - 3 * T) * T + 1) * P2
                + (T - 1) * T * T * P3) / 2

    segment = int(t * (len(control_points) - 3))
    t = (t * (len(control_points) - 3)) - segment
    p0, p1, p2, p3 = control_points[segment:segment+4]

    return interpolate(p0, p1, p2, p3, t)

#Calculates the gradient of two coordinates in format [x, y]
def gradient(coords1, coords2):
    return (coords2[1] - coords1[1]) / (coords2[0] - coords1[0])

#The class for a control point
class ControlPoint:
    def __init__(self, posX, posY):
        self.posX = posX
        self.posY = posY

        self.baseSize = 10
        self.size = self.baseSize

        self.pointSelected = False
        self.mouseHovering = False
        self.mouseDownLast = False

    #Returns the control point's pos in format [posX, posY]
    def getPos(self):
        return self.posX, self.posY

    #Calculates whether mouse is hovering, and whether user has selected point
    def update(self, mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame, offset, snap):
        self.mouseHovering = ((self.posX + (self.size + 2) > mousePosX > self.posX - (self.size + 2)) and
                               (self.posY + (self.size + 2) > mousePosY > self.posY - (self.size + 2)))

        if self.mouseHovering:
            self.size = self.baseSize + 2
        else:
            self.size = self.baseSize

        if not pygame.mouse.get_pressed()[0]:
            self.pointSelected = False

        if snap: roundValue = -1
        else: roundValue = 0

        if self.pointSelected:
            if screenBorder - offset[0] < mousePosX < screenWidth - screenBorder - offset[0]:
                self.posX = round(mousePosX, roundValue)

            if screenBorder - offset[1] < mousePosY < screenHeight - screenBorder - offset[1]:
                self.posY = round(mousePosY, roundValue)

        if not self.pointSelected:
            self.pointSelected = self.mouseHovering and pygame.mouse.get_pressed()[0] and not self.mouseDownLast

        self.mouseDownLast = pygame.mouse.get_pressed()[0]

    #Draws point to screen
    def draw(self, colour, screen, pygame, offset):
        pygame.draw.circle(screen, colour, (self.posX + offset[0], self.posY + offset[1]), self.size)

class Curve:
    def __init__(self, points = []):
        self.points = []
        self.splinePoints = []
        self.history = []
        self.pointsSelected = []
        self.mouseHovering = None

        for point in points:
            self.points.append(ControlPoint(point[0], point[1]))

    #Checks if current mouse pos crosses the spline (for inserting points)
    def mouseOnCurve(self, mousePosX, mousePosY, margin):
        for pointIndex in range(len(self.splinePoints)):
            if pointDistance((mousePosX, mousePosY), self.splinePoints[pointIndex]) <= margin:
                reconstructedT = (pointIndex / len(self.splinePoints))
                segment = int(reconstructedT * (len(self.points) - 1)) + 1
                return True, segment

        return False, None

    def add(self, anchorObject, index = -1):
        if index == -1:
            index = len(self.points)

        self.points.insert(index, anchorObject)
        self.computeSpline()

    def remove(self, index = -1):
        if index == -1:
            index = len(self.points) - 1

        if len(self.points) - 1 >= index:
            self.points.pop(index)
            self.computeSpline()

    def undo(self):
        print("Undo")

    def redo(self):
        print("Redo")

    def returnPointCoords(self):
        pointCoords = []
        for point in self.points:
            pointCoords.append(point.getPos())

        return pointCoords

    def computeSpline(self, perSegRes = 20, updatePoints = []):
        numOfSegments = len(self.points) - 1

        if len(self.points) >= 2:
            if len(updatePoints) > 0:
                self.splinePoints += [''] * ((numOfSegments * perSegRes) - len(self.splinePoints))
            else:
                self.splinePoints = [''] * (numOfSegments * perSegRes)


            resolution = numOfSegments * perSegRes
            updateRange = (0, resolution)

            if len(updatePoints) > 0:
                lowerBound = max((min(updatePoints) - 2), 0)
                upperBound = min(max(updatePoints) + 2, numOfSegments)
                updateRange = (lowerBound * perSegRes, upperBound * perSegRes)

            for tInt in range(*updateRange):
                t = tInt / resolution
                self.splinePoints[tInt] = (calculateSpline(self.returnPointCoords(), t))

    def update(self, mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame, offset, snap):
        self.pointsSelected = [point for point in self.points if point.pointSelected]

        self.mouseHovering = None
        for point in self.points:
            if point.mouseHovering: self.mouseHovering = self.points.index(point)

        for point in self.points:
            point.update(mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame, offset, snap)

        if len(self.pointsSelected) > 0:
            self.computeSpline(updatePoints = [self.points.index(point) for point in self.pointsSelected])

    def draw(self, programColours, screen, pygame, offset):
        for point in self.points:
            point.draw(programColours["controlPoint"], screen, pygame, offset)

        if len(self.points) >= 2:
            offsetCurve = [(point[0] + offset[0], point[1] + offset[1]) for point in self.splinePoints]
            pygame.draw.lines(screen, programColours["curve"], False, offsetCurve, 5)
