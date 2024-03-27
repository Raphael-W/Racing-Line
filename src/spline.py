import math
import numpy as np

#Calculates distance between 2 points
def pointDistance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    return math.sqrt(((y2 - y1) ** 2) + ((x1 - x2) ** 2))

def gradient(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    return abs((y2 - y1) / (x2 - x1))

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

def extendPoints(points):
    xExt = (points[-1][0] - points[-2][0])
    yExt = (points[-1][1] - points[-2][1])
    pointExt = (points[-1][0] + xExt, points[-1][1] + yExt)
    extendedSplinePoints = points + [pointExt]

    return extendedSplinePoints

def offsetPoints(points, offset):
    return [(point[0] + offset[0], point[1] + offset[1]) for point in points]

def calculateSide(points, pointIndex, width):
    width = width / 2
    points = extendPoints(points)

    distance = pointDistance(points[pointIndex], points[pointIndex + 1])
    sideX = ((width * (points[pointIndex][1] - points[pointIndex + 1][1])) / distance) + points[pointIndex][0]
    sideY = ((width * (points[pointIndex + 1][0] - points[pointIndex][0])) / distance) + points[pointIndex][1]

    return sideX, sideY

def formPolygon(leftSide, rightSide):
     return leftSide + list(reversed(rightSide))

def findKink(point, linePoints, width):
    width = width / 2

    kinkFound = False
    for pointIndex in range(len(linePoints)):
        kinkFound = kinkFound or (pointDistance(point, linePoints[pointIndex]) < (width - 1))
    return kinkFound


def calculateSpline(control_points, t):
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
        pygame.gfxdraw.aacircle(screen, self.posX + offset[0], self.posY + offset[1], self.size, colour)
        pygame.gfxdraw.filled_circle(screen, self.posX + offset[0], self.posY + offset[1], self.size, colour)

class Track:
    def __init__(self, points = []):
        self.points = []
        self.splinePoints = []

        self.splinePointsPolygonLeftSide = []
        self.splinePointsPolygonRightSide = []

        self.leftTrackEdgePolygonInner = []
        self.leftTrackEdgePolygonOuter = []

        self.rightTrackEdgePolygonInner = []
        self.rightTrackEdgePolygonOuter = []

        self.history = []
        self.pointsSelected = []
        self.mouseHovering = None
        self.closed = False

        self.perSegRes = 20
        self.width = 100

        for point in points:
            self.points.append(ControlPoint(point[0], point[1]))

    def changeWidth(self, value):
        self.width = value
        self.computeTrackEdges()

    def changeRes(self, value):
        self.perSegRes = int(value)
        self.computeSpline()
        self.computeTrackEdges()

    def updateCloseStatus(self, value):
        self.closed = value

    #Checks if current mouse pos crosses the spline (for inserting points)
    def mouseOnCurve(self, mousePosX, mousePosY, margin):
        for pointIndex in range(len(self.splinePoints) - 1):
            if lineToPointDistance(self.splinePoints[pointIndex], self.splinePoints[pointIndex + 1], (mousePosX, mousePosY)) <= margin:
                reconstructedT = (pointIndex / len(self.splinePoints))

                numOfPoints = len(self.points) - 1
                segment = int(reconstructedT * numOfPoints) + 1

                return True, segment
        return False, None

    def add(self, anchorObject, index = -1, update = True):
        if index == -1:
            index = len(self.points)

        self.points.insert(index, anchorObject)
        if len(self.points) > 1:
            if index > 0:
                self.splinePoints = self.splinePoints[:((index - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.splinePoints[((index - 1) * self.perSegRes):]
                self.splinePointsPolygonLeftSide = self.splinePointsPolygonLeftSide[:((index - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.splinePointsPolygonLeftSide[((index - 1) * self.perSegRes):]
                self.splinePointsPolygonRightSide = self.splinePointsPolygonRightSide[:((index - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.splinePointsPolygonRightSide[((index - 1) * self.perSegRes):]

                self.leftTrackEdgePolygonInner = self.leftTrackEdgePolygonInner[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.leftTrackEdgePolygonInner[((index - 1) * self.perSegRes):]
                self.leftTrackEdgePolygonOuter = self.leftTrackEdgePolygonOuter[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.leftTrackEdgePolygonOuter[((index - 1) * self.perSegRes):]

                self.rightTrackEdgePolygonInner = self.rightTrackEdgePolygonInner[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.rightTrackEdgePolygonInner[((index - 1) * self.perSegRes):]
                self.rightTrackEdgePolygonOuter = self.rightTrackEdgePolygonOuter[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.rightTrackEdgePolygonOuter[((index - 1) * self.perSegRes):]

            else:
                self.splinePoints = ([''] * self.perSegRes) + self.splinePoints
                self.splinePointsPolygonLeftSide = ([''] * self.perSegRes) + self.splinePointsPolygonLeftSide
                self.splinePointsPolygonRightSide = ([''] * self.perSegRes) + self.splinePointsPolygonRightSide

                self.leftTrackEdgePolygonInner = ([''] * self.perSegRes) + self.leftTrackEdgePolygonInner
                self.leftTrackEdgePolygonOuter = ([''] * self.perSegRes) + self.leftTrackEdgePolygonOuter

                self.rightTrackEdgePolygonInner = ([''] * self.perSegRes) + self.rightTrackEdgePolygonInner
                self.rightTrackEdgePolygonOuter = ([''] * self.perSegRes) + self.rightTrackEdgePolygonOuter

        if update:
            self.computeSpline(updatePoints = [index])
            self.computeTrackEdges(updatePoints = [index])

    def remove(self, index = -1, update = True):
        if index == -1:
            index = len(self.points) - 1

        if len(self.points) - 1 >= index:
            self.points.pop(index)

            if index > 0:
                self.splinePoints = self.splinePoints[:((index - 1) * self.perSegRes):] + self.splinePoints[(index * self.perSegRes):]
                self.splinePointsPolygonLeftSide = self.splinePointsPolygonLeftSide[:((index - 1) * self.perSegRes):] + self.splinePointsPolygonLeftSide[(index * self.perSegRes):]
                self.splinePointsPolygonRightSide = self.splinePointsPolygonRightSide[:((index - 1) * self.perSegRes):] + self.splinePointsPolygonRightSide[(index * self.perSegRes):]

                self.leftTrackEdgePolygonInner = self.leftTrackEdgePolygonInner[:((index - 1) * self.perSegRes)] + self.leftTrackEdgePolygonInner[(index * self.perSegRes):]
                self.leftTrackEdgePolygonOuter = self.leftTrackEdgePolygonOuter[:((index - 1) * self.perSegRes)] + self.leftTrackEdgePolygonOuter[(index * self.perSegRes):]

                self.rightTrackEdgePolygonInner = self.rightTrackEdgePolygonInner[:((index - 1) * self.perSegRes)] + self.rightTrackEdgePolygonInner[(index * self.perSegRes):]
                self.rightTrackEdgePolygonOuter = self.rightTrackEdgePolygonOuter[:((index - 1) * self.perSegRes)] + self.rightTrackEdgePolygonOuter[(index * self.perSegRes):]
            else:
                self.splinePoints = self.splinePoints[((index + 1) * self.perSegRes):]
                self.splinePointsPolygonLeftSide = self.splinePointsPolygonLeftSide[((index + 1) * self.perSegRes):]
                self.splinePointsPolygonRightSide = self.splinePointsPolygonRightSide[((index + 1) * self.perSegRes):]

                self.leftTrackEdgePolygonInner = self.leftTrackEdgePolygonInner[((index + 1) * self.perSegRes):]
                self.leftTrackEdgePolygonOuter = self.leftTrackEdgePolygonOuter[((index + 1) * self.perSegRes):]

                self.rightTrackEdgePolygonInner = self.rightTrackEdgePolygonInner[((index + 1) * self.perSegRes):]
                self.rightTrackEdgePolygonOuter = self.rightTrackEdgePolygonOuter[((index + 1) * self.perSegRes):]

            if update:
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
            if self.closed:
                first1 = self.points[1]
                first2 = self.points[2]
                last1 = self.points[-2]
                last2 = self.points[-3]

                self.add(last1, 0, False)
                self.add(last2, 0, False)
                self.add(first1, -1, False)
                self.add(first2, -1, False)

            numOfSegments = len(self.points) - 1
            resolution = numOfSegments * self.perSegRes

            updateRanges = []
            if self.closed and (0 in updatePoints) and (((len(self.points) - 1) - 4) in updatePoints):
                updatePoints.remove(0)

            for point in updatePoints:
                if len(updatePoints) > 0:
                    if self.closed:
                        lengthPoints = (len(self.points) - 1) - 4
                        point += 2

                        beforeJoinLowerBound = max(point - 2, 2)
                        beforeJoinUpperBound = min(point + 2, lengthPoints + 2)
                        beforeJoinUpdateRange = [beforeJoinLowerBound * self.perSegRes, beforeJoinUpperBound * self.perSegRes]

                        afterJoinLowerBound = max((point + lengthPoints) - 2, 2)
                        afterJoinUpperBound = min((point + lengthPoints) + 2, lengthPoints + 2)
                        afterJoinUpdateRange = [afterJoinLowerBound * self.perSegRes, afterJoinUpperBound * self.perSegRes]

                        if afterJoinLowerBound >= (lengthPoints + 2):
                            afterJoinLowerBound = max((point - lengthPoints) - 2, 2)
                            afterJoinUpperBound = max(min((point - lengthPoints) + 2, lengthPoints + 2), 2)
                            afterJoinUpdateRange = [afterJoinLowerBound * self.perSegRes, afterJoinUpperBound * self.perSegRes]

                        updateRanges.append(beforeJoinUpdateRange)
                        updateRanges.append(afterJoinUpdateRange)

                    else:
                        lowerBound = max(point - 2, 0)
                        upperBound = min(point + 2, numOfSegments)
                        updateRange = (lowerBound * self.perSegRes, upperBound * self.perSegRes)

                        updateRanges.append(updateRange)

            if len(updateRanges) == 0:
                updateRanges = [(0, resolution)]
                self.splinePoints = ([''] * resolution)

            for updateRange in updateRanges:
                for tInt in range(*updateRange):
                    t = tInt / resolution
                    self.splinePoints[tInt] = (calculateSpline(self.returnPointCoords(), t))

            if self.closed:
                self.remove(0, False)
                self.remove(0, False)
                self.remove(-1, False)
                self.remove(-1, False)

    def computeTrackEdges(self, updatePoints = []):
        if len(self.points) >= 2:
            numOfSegments = len(self.points) - 1
            resolution = numOfSegments * self.perSegRes

            updateRanges = []
            for point in updatePoints:
                if len(updatePoints) > 0:
                    if self.closed:
                        lengthPoints = (len(self.points) - 1)

                        beforeJoinLowerBound = max(point - 2, 0)
                        beforeJoinUpperBound = min(point + 2, lengthPoints)
                        beforeJoinUpdateRange = [beforeJoinLowerBound * self.perSegRes, beforeJoinUpperBound * self.perSegRes]

                        afterJoinLowerBound = max((point + lengthPoints) - 2, 0)
                        afterJoinUpperBound = min((point + lengthPoints) + 2, lengthPoints)
                        afterJoinUpdateRange = [afterJoinLowerBound * self.perSegRes, afterJoinUpperBound * self.perSegRes]

                        if afterJoinLowerBound >= (lengthPoints + 2):
                            afterJoinLowerBound = max((point - lengthPoints) - 2, 0)
                            afterJoinUpperBound = max(min((point - lengthPoints) + 2, lengthPoints), 0)
                            afterJoinUpdateRange = [afterJoinLowerBound * self.perSegRes, afterJoinUpperBound * self.perSegRes]

                        updateRanges.append(beforeJoinUpdateRange)
                        updateRanges.append(afterJoinUpdateRange)

                    else:
                        lowerBound = max(point - 2, 0)
                        upperBound = min(point + 2, numOfSegments)
                        updateRange = (lowerBound * self.perSegRes, upperBound * self.perSegRes)

                        updateRanges.append(updateRange)

            if len(updatePoints) == 0:
                updateRanges = [(0, resolution)]

                self.splinePointsPolygonLeftSide = ([''] * resolution)
                self.splinePointsPolygonRightSide = ([''] * resolution)

                self.leftTrackEdgePolygonInner = ([''] * resolution)
                self.leftTrackEdgePolygonOuter = ([''] * resolution)

                self.rightTrackEdgePolygonInner = ([''] * resolution)
                self.rightTrackEdgePolygonOuter = ([''] * resolution)

            for updateRange in updateRanges:
                for point in range(*updateRange):
                    self.splinePointsPolygonLeftSide[point] = calculateSide(self.splinePoints, point, 5)
                    self.splinePointsPolygonRightSide[point] = calculateSide(self.splinePoints, point, -5)

                    self.leftTrackEdgePolygonInner[point] = calculateSide(self.splinePoints, point, self.width)
                    self.leftTrackEdgePolygonOuter[point] = calculateSide(self.splinePoints, point, self.width + 20)

                    self.rightTrackEdgePolygonInner[point] = calculateSide(self.splinePoints, point, -self.width)
                    self.rightTrackEdgePolygonOuter[point] = calculateSide(self.splinePoints, point, -(self.width + 20))

    def computeKerbs(self, pygame, screen):
        kerbThreshold = 0.08
        if len(self.points) >= 2:
            lengthOfSpline = len(self.splinePoints) - 1
            previousGrad = gradient(self.splinePoints[0], self.splinePoints[1])
            kerbRanges = []

            lowerBound = None
            upperBound = None

            for dot in range(lengthOfSpline):
                currentGrad = gradient(self.splinePoints[dot], self.splinePoints[dot + 1])
                diffInGrad = (previousGrad - currentGrad) / previousGrad
                if diffInGrad > kerbThreshold:
                    if lowerBound is None:
                        lowerBound = dot
                else:
                    if lowerBound is not None:
                        upperBound = dot
                        kerbRanges.append((lowerBound, upperBound))

                        lowerBound = None
                        upperBound = None

                previousGrad = currentGrad

            for kerbRange in kerbRanges:
                for dot in range(*kerbRange):
                    pygame.draw.circle(screen, (252, 186, 3), self.splinePoints[dot], 5)

    def deKink(self):
        extendedSplinePoints = extendPoints(self.splinePoints)

        updateRange = (0, len(self.splinePoints))
        nonKinkCoordLeftInner = self.leftTrackEdgePolygonInner[0]
        nonKinkCoordLeftOuter = self.leftTrackEdgePolygonOuter[0]

        nonKinkCoordRightInner = self.rightTrackEdgePolygonInner[0]
        nonKinkCoordRightOuter = self.rightTrackEdgePolygonOuter[0]

        for seg in range(*updateRange):
            detectionRange = (max(seg - (2 * self.perSegRes), 0), min(seg + (2 * self.perSegRes), len(self.leftTrackEdgePolygonInner)))
            if findKink(self.leftTrackEdgePolygonInner[seg], extendedSplinePoints[detectionRange[0]: detectionRange[1]], self.width):
                self.leftTrackEdgePolygonInner[seg] = nonKinkCoordLeftInner
                self.leftTrackEdgePolygonOuter[seg] = nonKinkCoordLeftOuter
            else:
                nonKinkCoordLeftInner = self.leftTrackEdgePolygonInner[seg]
                nonKinkCoordLeftOuter = self.leftTrackEdgePolygonOuter[seg]

            if findKink(self.rightTrackEdgePolygonInner[seg], extendedSplinePoints[detectionRange[0]: detectionRange[1]], self.width):
                self.rightTrackEdgePolygonInner[seg] = nonKinkCoordRightInner
                self.rightTrackEdgePolygonOuter[seg] = nonKinkCoordRightOuter
            else:
                nonKinkCoordRightInner = self.rightTrackEdgePolygonInner[seg]
                nonKinkCoordRightOuter = self.rightTrackEdgePolygonOuter[seg]

    def update(self, mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame, offset, snap):
        self.pointsSelected = [[self.points[point], point] for point in range(len(self.points)) if self.points[point].pointSelected]

        for point in range(len(self.pointsSelected)):
            if not(point == 0 or (((self.pointsSelected[point][1] == 0) or (self.pointsSelected[point][1] == len(self.points) - 1)) and self.closed)):
                self.pointsSelected[point][0].pointSelected = False

        if self.closed and self.points[0].pointSelected:
            self.points[-1].pointSelected = True

        elif self.closed and self.points[-1].pointSelected:
            self.points[0].pointSelected = True

        self.mouseHovering = None
        for point in self.points:
            if point.mouseHovering: self.mouseHovering = self.points.index(point)

        for point in self.points:
            point.update(mousePosX, mousePosY, screenWidth, screenHeight, screenBorder, pygame, offset, snap)

        if len(self.points) >= 4:
            snapThreshold = 50
            if self.points[0].pointSelected and (-snapThreshold <= self.points[0].posX - self.points[-1].posX <= snapThreshold) and (-snapThreshold <= self.points[0].posY - self.points[-1].posY <= snapThreshold) and not(pygame.key.get_mods() & pygame.KMOD_LSHIFT):
                self.points[0].posX, self.points[0].posY = self.points[-1].posX, self.points[-1].posY
                self.updateCloseStatus(value = True)

            elif self.points[-1].pointSelected and (-snapThreshold <= self.points[-1].posX - self.points[0].posX <= snapThreshold) and (-snapThreshold <= self.points[-1].posY - self.points[0].posY <= snapThreshold) and not(pygame.key.get_mods() & pygame.KMOD_LSHIFT):
                self.points[-1].posX, self.points[-1].posY = self.points[0].posX, self.points[0].posY
                self.updateCloseStatus(value = True)

            if (self.points[0].pointSelected or self.points[-1].pointSelected) and (pygame.key.get_mods() & pygame.KMOD_LSHIFT):
                self.updateCloseStatus(value = False)

        else:
            self.updateCloseStatus(value = False)

        if len(self.pointsSelected) > 0:
            updatePoints = [point[1] for point in self.pointsSelected]

            self.computeSpline(updatePoints = updatePoints)
            self.computeTrackEdges(updatePoints = updatePoints)

    def draw(self, programColours, screen, pygame, offset, switchFront):
        if len(self.points) >= 2:
            splinePointsPolygonLeftSideOffset = offsetPoints(self.splinePointsPolygonLeftSide, offset)
            splinePointsPolygonRightSideOffset = offsetPoints(self.splinePointsPolygonRightSide, offset)

            leftTrackEdgePolygonInnerOffset = offsetPoints(self.leftTrackEdgePolygonInner, offset)
            leftTrackEdgePolygonOuterOffset = offsetPoints(self.leftTrackEdgePolygonOuter, offset)

            rightTrackEdgePolygonInnerOffset = offsetPoints(self.rightTrackEdgePolygonInner, offset)
            rightTrackEdgePolygonOuterOffset = offsetPoints(self.rightTrackEdgePolygonOuter, offset)

            for point in range(len(self.points) - 1):
                leftTrackEdgePolygonInnerSegment = leftTrackEdgePolygonInnerOffset[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]
                leftTrackEdgePolygonOuterSegment = leftTrackEdgePolygonOuterOffset[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]

                rightTrackEdgePolygonInnerSegment = rightTrackEdgePolygonInnerOffset[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]
                rightTrackEdgePolygonOuterSegment = rightTrackEdgePolygonOuterOffset[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]

                if (point == len(self.points) - 2) and self.closed:
                    leftTrackEdgePolygonInnerSegment.append(leftTrackEdgePolygonInnerOffset[0])
                    leftTrackEdgePolygonOuterSegment.append(leftTrackEdgePolygonOuterOffset[0])

                    rightTrackEdgePolygonInnerSegment.append(rightTrackEdgePolygonInnerOffset[0])
                    rightTrackEdgePolygonOuterSegment.append(rightTrackEdgePolygonOuterOffset[0])

                leftTrackEdgePolygon = formPolygon(leftTrackEdgePolygonInnerSegment, leftTrackEdgePolygonOuterSegment)
                rightTrackEdgePolygon = formPolygon(rightTrackEdgePolygonInnerSegment, rightTrackEdgePolygonOuterSegment)

                pygame.gfxdraw.aapolygon(screen, leftTrackEdgePolygon, programColours["white"])
                pygame.gfxdraw.filled_polygon(screen, leftTrackEdgePolygon, programColours["white"])

                pygame.gfxdraw.aapolygon(screen, rightTrackEdgePolygon, programColours["white"])
                pygame.gfxdraw.filled_polygon(screen, rightTrackEdgePolygon, programColours["white"])

            for point in range(len(self.points) - 1):
                leftTrackEdgePolygonInnerSegment = leftTrackEdgePolygonInnerOffset[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]
                rightTrackEdgePolygonInnerSegment = rightTrackEdgePolygonInnerOffset[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]

                if (point == len(self.points) - 2) and self.closed:
                    leftTrackEdgePolygonInnerSegment.append(leftTrackEdgePolygonInnerOffset[0])
                    rightTrackEdgePolygonInnerSegment.append(rightTrackEdgePolygonInnerOffset[0])

                mainTrackPolygon = formPolygon(leftTrackEdgePolygonInnerSegment, rightTrackEdgePolygonInnerSegment)

                # pygame.gfxdraw.aapolygon(screen, mainTrackPolygon, programColours["mainTrack"])
                # pygame.gfxdraw.filled_polygon(screen, mainTrackPolygon, programColours["mainTrack"])

            for point in range(len(self.points) - 1):
                splinePointsPolygonLeftSideOffsetSegment = splinePointsPolygonLeftSideOffset[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]
                splinePointsPolygonRightSideOffsetSegment = splinePointsPolygonRightSideOffset[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]

                if (point == len(self.points) - 2) and self.closed:
                    splinePointsPolygonLeftSideOffsetSegment.append(splinePointsPolygonLeftSideOffset[0])
                    splinePointsPolygonRightSideOffsetSegment.append(splinePointsPolygonRightSideOffset[0])

                mainCurvePolygon = formPolygon(splinePointsPolygonLeftSideOffsetSegment, splinePointsPolygonRightSideOffsetSegment)

                pygame.gfxdraw.aapolygon(screen, mainCurvePolygon, programColours["curve"])
                pygame.gfxdraw.filled_polygon(screen, mainCurvePolygon, programColours["curve"])

            # for i in offsetMainCurve:
            #     pygame.draw.circle(screen, programColours["curve"], i, 5)

        for point in range(len(self.points)):

            if (not switchFront and point == len(self.points) - 1) or (switchFront and point == 0) or (self.closed and ((point == 0) or (point == len(self.points) - 1))):
                colour = programColours["frontControlPoint"]
            else:
                colour = programColours["controlPoint"]

            self.points[point].draw(colour, screen, pygame, offset)
