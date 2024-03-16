import math
import numpy as np

#Calculates distance between 2 points
def pointDistance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    return math.sqrt(((y2 - y1) ** 2) + ((x1 - x2) ** 2))

def lineToPointDistance(lineA, lineB, point):
    lineA = np.array(lineA)
    lineB = np.array(lineB)
    point = np.array(point)

    l2 = pointDistance(lineA, lineB) ** 2
    if l2 == 0:
        return pointDistance(point, lineA)

    t = max(0, min(1, np.dot(point - lineA, lineB - lineA) / l2))
    projection = lineA + t * (lineB - lineA)
    return pointDistance(point, projection)

def findKink(point, linePoints, width):
    kinkFound = False
    for pointIndex in range(len(linePoints)):
        kinkFound = kinkFound or (pointDistance(point, linePoints[pointIndex]) < (width - 1))
    return kinkFound


#Returns a position on the curve given t and the control points
def calculateSpline(control_points, t, closed = False):
    control_points = [control_points[1]] + control_points + [control_points[-2]]

    #Interpolate curve using Catmull Rom
    def interpolate(P0, P1, P2, P3, T):

        P0 = np.array(P0)
        P1 = np.array(P1)
        P2 = np.array(P2)
        P3 = np.array(P3)

        return (
            T * ((2 - T) * T - 1) * P0
            + (T * T * (3 * T - 5) + 2) * P1
            + T * ((4 - 3 * T) * T + 1) * P2
            + (T - 1) * T * T * P3) / 2

    segment = int(t * (len(control_points) - 3))
    t = (t * (len(control_points) - 3)) - segment
    p0, p1, p2, p3 = control_points[segment:segment+4]

    return interpolate(p0, p1, p2, p3, t)

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

class Track:
    def __init__(self, points = []):
        self.points = []
        self.splinePoints = []

        self.leftTrackEdge = []
        self.rightTrackEdge = []

        self.history = []
        self.pointsSelected = []
        self.mouseHovering = None
        self.closed = False

        self.perSegRes = 20
        self.width = 50

        for point in points:
            self.points.append(ControlPoint(point[0], point[1]))

    def closeTrack(self, newValue):
        self.closed = newValue

        self.computeSpline(updatePoints = [])
        self.computeTrackEdges(updatePoints = [])

    #Checks if current mouse pos crosses the spline (for inserting points)
    def mouseOnCurve(self, mousePosX, mousePosY, margin):
        for pointIndex in range(len(self.splinePoints) - 1):
            if lineToPointDistance(self.splinePoints[pointIndex], self.splinePoints[pointIndex + 1], (mousePosX, mousePosY)) <= margin:
                reconstructedT = (pointIndex / len(self.splinePoints))
                segment = int(reconstructedT * (len(self.points) - 1)) + 1
                return True, segment

        return False, None

    def add(self, anchorObject, index = -1):
        if index == -1:
            index = len(self.points)

        self.points.insert(index, anchorObject)
        self.computeSpline(updatePoints = [index])
        self.computeTrackEdges(updatePoints = [index])

    def remove(self, index = -1):
        if index == -1:
            index = len(self.points) - 1

        if len(self.points) - 1 >= index:
            self.points.pop(index)
            self.computeSpline(updatePoints = [index])
            self.computeTrackEdges(updatePoints = [index])

    def undo(self):
        print("Undo")

    def redo(self):
        print("Redo")

    def returnPointCoords(self):
        pointCoords = []
        for point in self.points:
            pointCoords.append(point.getPos())

        return pointCoords

    def computeSpline(self, updatePoints = []):
        if len(self.points) >= 2:
            numOfSegments = len(self.points) - 1

            if len(updatePoints) > 0:
                if (numOfSegments * self.perSegRes) > len(self.splinePoints):
                    for point in updatePoints:
                        if point > 0:
                            self.splinePoints = self.splinePoints[:((point - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.splinePoints[((point - 1) * self.perSegRes):]
                        else:
                            self.splinePoints = ([''] * self.perSegRes) + self.splinePoints

                elif (numOfSegments * self.perSegRes) < len(self.splinePoints):
                    for point in updatePoints:
                        if point > 0:
                            self.splinePoints = self.splinePoints[:((point - 1) * self.perSegRes):] + self.splinePoints[(point * self.perSegRes):]
                        else:
                            self.splinePoints = self.splinePoints[((point + 1) * self.perSegRes):]

            else:
                self.splinePoints = [''] * (numOfSegments * self.perSegRes)

            resolution = numOfSegments * self.perSegRes
            updateRange = (0, resolution)
            if len(updatePoints) > 0:
                lowerBound = max((min(updatePoints) - 2, 0))
                upperBound = min(max(updatePoints) + 2, numOfSegments)
                updateRange = (lowerBound * self.perSegRes, upperBound * self.perSegRes)

            for tInt in range(*updateRange):
                t = tInt / resolution
                self.splinePoints[tInt] = (calculateSpline(self.returnPointCoords(), t, self.closed))

    def computeTrackEdges(self, updatePoints = []):
        if len(self.splinePoints) >= 2:
            if len(updatePoints) > 0:
                if len(self.splinePoints) > len(self.leftTrackEdge):
                    for point in updatePoints:
                        if point > 0:
                            self.leftTrackEdge = self.leftTrackEdge[:((point - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.leftTrackEdge[((point - 1) * self.perSegRes):]
                            self.rightTrackEdge = self.rightTrackEdge[:((point - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.rightTrackEdge[((point - 1) * self.perSegRes):]
                        else:
                            self.leftTrackEdge = ([''] * self.perSegRes) + self.leftTrackEdge
                            self.rightTrackEdge = ([''] * self.perSegRes) + self.rightTrackEdge

                elif len(self.splinePoints) < len(self.leftTrackEdge):
                    for point in updatePoints:
                        if point > 0:
                            self.leftTrackEdge = self.leftTrackEdge[:((point - 1) * self.perSegRes)] + self.leftTrackEdge[(point * self.perSegRes):]
                            self.rightTrackEdge = self.rightTrackEdge[:((point - 1) * self.perSegRes)] + self.rightTrackEdge[(point * self.perSegRes):]
                        else:
                            self.leftTrackEdge = self.leftTrackEdge[((point + 1) * self.perSegRes):]
                            self.rightTrackEdge = self.rightTrackEdge[((point + 1) * self.perSegRes):]

            else:
                self.leftTrackEdge = [''] * (len(self.splinePoints))
                self.rightTrackEdge = [''] * (len(self.splinePoints))

            updateRange = (0, len(self.splinePoints))
            if len(updatePoints) > 0:
                lowerBound = max((min(updatePoints) - 2) * self.perSegRes, 0)
                upperBound = min((max(updatePoints) + 2) * self.perSegRes, len(self.splinePoints))
                updateRange = (lowerBound, upperBound)

            xExt = (self.splinePoints[-1][0] - self.splinePoints[-2][0])
            yExt = (self.splinePoints[-1][1] - self.splinePoints[-2][1])
            pointExt = (self.splinePoints[-1][0] + xExt, self.splinePoints[-1][1] + yExt)
            extendedSplinePoints = self.splinePoints + [pointExt]

            for seg in range(*updateRange):
                distance = pointDistance(extendedSplinePoints[seg], extendedSplinePoints[seg + 1])

                newXLeft = ((self.width * (extendedSplinePoints[seg][1] - extendedSplinePoints[seg + 1][1])) / distance) + extendedSplinePoints[seg][0]
                newYLeft = ((self.width * (extendedSplinePoints[seg + 1][0] - extendedSplinePoints[seg][0])) / distance) + extendedSplinePoints[seg][1]

                newXRight = ((-self.width * (extendedSplinePoints[seg][1] - extendedSplinePoints[seg + 1][1])) / distance) + extendedSplinePoints[seg][0]
                newYRight = ((-self.width * (extendedSplinePoints[seg + 1][0] - extendedSplinePoints[seg][0])) / distance) + extendedSplinePoints[seg][1]

                self.leftTrackEdge[seg] = (newXLeft, newYLeft)
                self.rightTrackEdge[seg] = (newXRight, newYRight)

    def deKink(self):
        xExt = (self.splinePoints[-1][0] - self.splinePoints[-2][0])
        yExt = (self.splinePoints[-1][1] - self.splinePoints[-2][1])
        pointExt = (self.splinePoints[-1][0] + xExt, self.splinePoints[-1][1] + yExt)
        extendedSplinePoints = self.splinePoints + [pointExt]

        updateRange = (0, len(self.splinePoints))
        nonKinkCoordLeft = self.leftTrackEdge[0]
        nonKinkCoordRight = self.rightTrackEdge[0]

        for seg in range(*updateRange):
            detectionRange = (max(seg - (2 * self.perSegRes), 0), min(seg + (2 * self.perSegRes), len(self.leftTrackEdge)))
            if findKink(self.leftTrackEdge[seg], extendedSplinePoints[detectionRange[0]: detectionRange[1]], self.width):
                self.leftTrackEdge[seg] = nonKinkCoordLeft
            else:
                nonKinkCoordLeft = self.leftTrackEdge[seg]

            if findKink(self.rightTrackEdge[seg], extendedSplinePoints[detectionRange[0]: detectionRange[1]], self.width):
                self.rightTrackEdge[seg] = nonKinkCoordRight
            else:
                nonKinkCoordRight = self.rightTrackEdge[seg]

    def update(self, mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame, offset, snap):
        self.pointsSelected = [point for point in self.points if point.pointSelected]

        for point in range(len(self.pointsSelected)):
            if not(point == 0):
                self.pointsSelected[point].pointSelected = False

        self.mouseHovering = None
        for point in self.points:
            if point.mouseHovering: self.mouseHovering = self.points.index(point)

        for point in self.points:
            point.update(mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame, offset, snap)

        if len(self.pointsSelected) > 0:
            updatePoints = [self.points.index(point) for point in self.pointsSelected]

            self.computeSpline(updatePoints = updatePoints)
            self.computeTrackEdges(updatePoints = updatePoints)

    def draw(self, programColours, screen, pygame, offset, switchFront):
        if len(self.points) >= 2:
            offsetMainCurve = [(point[0] + offset[0], point[1] + offset[1]) for point in self.splinePoints]
            offsetLeftTrackEdge = [(point[0] + offset[0], point[1] + offset[1]) for point in self.leftTrackEdge]
            offsetRightTrackEdge = [(point[0] + offset[0], point[1] + offset[1]) for point in self.rightTrackEdge]

            pygame.draw.lines(screen, (200, 200, 200), False, offsetLeftTrackEdge, 20)
            pygame.draw.lines(screen, (200, 200, 200), False, offsetRightTrackEdge, 20)

            for point in range(len(self.points) - 1):
                overlapIndex = 1
                if point == 0:
                    overlapIndex = 0

                leftTrackSegment = offsetLeftTrackEdge[(point * self.perSegRes) - overlapIndex:((point + 1) * self.perSegRes)]
                rightTrackSegment = offsetRightTrackEdge[(point * self.perSegRes) - overlapIndex:((point + 1) * self.perSegRes)]
                combinedTrackEdges = leftTrackSegment + list(reversed(rightTrackSegment))

                pygame.draw.polygon(screen, (100, 100, 100), combinedTrackEdges)

            pygame.draw.lines(screen, programColours["curve"], False, offsetMainCurve, 5)

        for point in range(len(self.points)):
            colour = programColours["controlPoint"]
            if (not switchFront and point == len(self.points) - 1) or (switchFront and point == 0):
                colour = programColours["frontControlPoint"]

            self.points[point].draw(colour, screen, pygame, offset)
