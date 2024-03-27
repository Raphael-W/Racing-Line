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

def findKink(point, linePoints, width):
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
                self.leftTrackEdge = self.leftTrackEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.leftTrackEdge[((index - 1) * self.perSegRes):]
                self.rightTrackEdge = self.rightTrackEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.rightTrackEdge[((index - 1) * self.perSegRes):]
            else:
                self.splinePoints = ([''] * self.perSegRes) + self.splinePoints
                self.leftTrackEdge = ([''] * self.perSegRes) + self.leftTrackEdge
                self.rightTrackEdge = ([''] * self.perSegRes) + self.rightTrackEdge

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
                self.leftTrackEdge = self.leftTrackEdge[:((index - 1) * self.perSegRes)] + self.leftTrackEdge[(index * self.perSegRes):]
                self.rightTrackEdge = self.rightTrackEdge[:((index - 1) * self.perSegRes)] + self.rightTrackEdge[(index * self.perSegRes):]
            else:
                self.splinePoints = self.splinePoints[((index + 1) * self.perSegRes):]
                self.leftTrackEdge = self.leftTrackEdge[((index + 1) * self.perSegRes):]
                self.rightTrackEdge = self.rightTrackEdge[((index + 1) * self.perSegRes):]

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
                self.leftTrackEdge = [''] * (len(self.splinePoints))
                self.rightTrackEdge = [''] * (len(self.splinePoints))

            xExt = (self.splinePoints[-1][0] - self.splinePoints[-2][0])
            yExt = (self.splinePoints[-1][1] - self.splinePoints[-2][1])
            pointExt = (self.splinePoints[-1][0] + xExt, self.splinePoints[-1][1] + yExt)
            extendedSplinePoints = self.splinePoints + [pointExt]

            for updateRange in updateRanges:
                for seg in range(*updateRange):
                    distance = pointDistance(extendedSplinePoints[seg], extendedSplinePoints[seg + 1])

                    newXLeft = ((self.width * (extendedSplinePoints[seg][1] - extendedSplinePoints[seg + 1][1])) / distance) + extendedSplinePoints[seg][0]
                    newYLeft = ((self.width * (extendedSplinePoints[seg + 1][0] - extendedSplinePoints[seg][0])) / distance) + extendedSplinePoints[seg][1]

                    newXRight = ((-self.width * (extendedSplinePoints[seg][1] - extendedSplinePoints[seg + 1][1])) / distance) + extendedSplinePoints[seg][0]
                    newYRight = ((-self.width * (extendedSplinePoints[seg + 1][0] - extendedSplinePoints[seg][0])) / distance) + extendedSplinePoints[seg][1]

                    self.leftTrackEdge[seg] = (newXLeft, newYLeft)
                    self.rightTrackEdge[seg] = (newXRight, newYRight)

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
            offsetMainCurve = [(point[0] + offset[0], point[1] + offset[1]) for point in self.splinePoints]

            offsetLeftTrackEdge = [(point[0] + offset[0], point[1] + offset[1]) for point in self.leftTrackEdge]
            offsetRightTrackEdge = [(point[0] + offset[0], point[1] + offset[1]) for point in self.rightTrackEdge]

            if self.closed:
                offsetMainCurve.append(offsetMainCurve[0])
                offsetLeftTrackEdge.append(offsetLeftTrackEdge[0])
                offsetRightTrackEdge.append(offsetRightTrackEdge[0])

            pygame.draw.lines(screen, (200, 200, 200), False, offsetLeftTrackEdge, 20)
            pygame.draw.lines(screen, (200, 200, 200), False, offsetRightTrackEdge, 20)

            for point in range(len(self.points) - 1):
                leftTrackSegment = offsetLeftTrackEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]
                rightTrackSegment = offsetRightTrackEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1]
                combinedTrackEdges = leftTrackSegment + list(reversed(rightTrackSegment))

                pygame.draw.polygon(screen, (100, 100, 100), combinedTrackEdges)

            pygame.draw.lines(screen, programColours["curve"], False, offsetMainCurve, 5)

            # for i in offsetMainCurve:
            #     pygame.draw.circle(screen, programColours["curve"], i, 5)

        for point in range(len(self.points)):

            if (not switchFront and point == len(self.points) - 1) or (switchFront and point == 0) or (self.closed and ((point == 0) or (point == len(self.points) - 1))):
                colour = programColours["frontControlPoint"]
            else:
                colour = programColours["controlPoint"]

            self.points[point].draw(colour, screen, pygame, offset)
