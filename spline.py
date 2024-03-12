import math
import numpy as np

#Calculates distance between 2 points
def pointDistance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    return math.sqrt(((y2 - y1) ** 2) + ((x1 - x2) ** 2))

def findKink(point, linePoints, width):
    kinkFound = False
    for pointIndex in range(len(linePoints)):
        kinkFound = kinkFound or (pointDistance(point, linePoints[pointIndex]) < width)
    return kinkFound


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

class Track:
    def __init__(self, points = []):
        self.points = []
        self.splinePoints = []

        self.leftTrackEdge = []
        self.rightTrackEdge = []

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

    def computeSpline(self, perSegRes = 20, updatePoints = []):
        numOfSegments = len(self.points) - 1

        if len(self.points) >= 2:
            if len(updatePoints) > 0:
                if (numOfSegments * perSegRes) > len(self.splinePoints):
                    for point in updatePoints:
                        self.splinePoints = self.splinePoints[:((point - 1) * perSegRes):] + ([''] * perSegRes) + self.splinePoints[((point - 1) * perSegRes):]

                elif (numOfSegments * perSegRes) < len(self.splinePoints):
                    for point in updatePoints:
                        self.splinePoints = self.splinePoints[:((point - 1) * perSegRes):] + self.splinePoints[(point * perSegRes):]

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

    def computeTrackEdges(self, perSegRes = 20, updatePoints = [], width = 50):
        if len(self.splinePoints) >= 2:
            if len(updatePoints) > 0:
                if len(self.splinePoints) > len(self.leftTrackEdge):
                    for point in updatePoints:
                        self.leftTrackEdge = self.leftTrackEdge[:((point - 1) * perSegRes)] + ([''] * perSegRes) + self.leftTrackEdge[((point - 1) * perSegRes):]
                        self.rightTrackEdge = self.rightTrackEdge[:((point - 1) * perSegRes)] + ([''] * perSegRes) + self.rightTrackEdge[((point - 1) * perSegRes):]

                elif len(self.splinePoints) < len(self.leftTrackEdge):
                    for point in updatePoints:
                        self.leftTrackEdge = self.leftTrackEdge[:((point - 1) * perSegRes)] + self.leftTrackEdge[(point * perSegRes):]
                        self.rightTrackEdge = self.rightTrackEdge[:((point - 1) * perSegRes)] + self.rightTrackEdge[(point * perSegRes):]

            else:
                self.leftTrackEdge = [''] * (len(self.splinePoints))
                self.rightTrackEdge = [''] * (len(self.splinePoints))

            updateRange = (0, len(self.splinePoints))
            if len(updatePoints) > 0:
                lowerBound = max((min(updatePoints) - 2) * perSegRes, 0)
                upperBound = min((max(updatePoints) + 2) * perSegRes, len(self.splinePoints))
                updateRange = (lowerBound, upperBound)

            nonKinkCoordLeft = (0, 0)
            nonKinkCoordRight = (0, 0)

            xExt = (self.splinePoints[-1][0] - self.splinePoints[-2][0])
            yExt = (self.splinePoints[-1][1] - self.splinePoints[-2][1])
            pointExt = (self.splinePoints[-1][0] + xExt, self.splinePoints[-1][1] + yExt)
            extendedSplinePoints = self.splinePoints + [pointExt]

            for seg in range(*updateRange):
                distance = pointDistance(extendedSplinePoints[seg], extendedSplinePoints[seg + 1])

                newXLeft = ((width * (extendedSplinePoints[seg][1] - extendedSplinePoints[seg + 1][1])) / distance) + extendedSplinePoints[seg][0]
                newYLeft = ((width * (extendedSplinePoints[seg + 1][0] - extendedSplinePoints[seg][0])) / distance) + extendedSplinePoints[seg][1]

                newXRight = ((-width * (extendedSplinePoints[seg][1] - extendedSplinePoints[seg + 1][1])) / distance) + extendedSplinePoints[seg][0]
                newYRight = ((-width * (extendedSplinePoints[seg + 1][0] - extendedSplinePoints[seg][0])) / distance) + extendedSplinePoints[seg][1]

                if findKink((newXLeft, newYLeft), extendedSplinePoints[updateRange[0]: updateRange[1]], width - 3):
                    newXLeft, newYLeft = nonKinkCoordLeft
                else:
                    nonKinkCoordLeft = (newXLeft, newYLeft)

                if findKink((newXRight, newYRight), extendedSplinePoints[updateRange[0]: updateRange[1]], width - 3):
                    newXRight, newYRight = nonKinkCoordRight
                else:
                    nonKinkCoordRight = (newXRight, newYRight)

                self.leftTrackEdge[seg] = (newXLeft, newYLeft)
                self.rightTrackEdge[seg] = (newXRight, newYRight)
            print(self.leftTrackEdge)

    def update(self, mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame, offset, snap):
        self.pointsSelected = [point for point in self.points if point.pointSelected]
        for point in self.pointsSelected[1:]:
            point.pointSelected = False

        self.mouseHovering = None
        for point in self.points:
            if point.mouseHovering: self.mouseHovering = self.points.index(point)

        for point in self.points:
            point.update(mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame, offset, snap)

        if len(self.pointsSelected) > 0:
            updatePoints = [self.points.index(point) for point in self.pointsSelected]
            self.computeSpline(updatePoints = updatePoints)
            self.computeTrackEdges(updatePoints = updatePoints, width = 50)


    def draw(self, programColours, screen, pygame, offset):
        if len(self.points) >= 2:
            offsetMainCurve = [(point[0] + offset[0], point[1] + offset[1]) for point in self.splinePoints]
            offsetLeftTrackEdge = [(point[0] + offset[0], point[1] + offset[1]) for point in self.leftTrackEdge]
            offsetRightTrackEdge = [(point[0] + offset[0], point[1] + offset[1]) for point in self.rightTrackEdge]

            combinedTrackEdges = offsetLeftTrackEdge + list(reversed(offsetRightTrackEdge))

            pygame.draw.polygon(screen, (100, 100, 100), combinedTrackEdges)
            pygame.draw.lines(screen, programColours["curve"], False, offsetMainCurve, 5)
            pygame.draw.lines(screen, (200, 200, 200), False, offsetLeftTrackEdge, 10)
            pygame.draw.lines(screen, (200, 200, 200), False, offsetRightTrackEdge, 10)

        for point in self.points:
            point.draw(programColours["controlPoint"], screen, pygame, offset)
