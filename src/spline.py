from utils import *
from history import *

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

        self.new = True
        self.pointSelected = False
        self.mouseHovering = False
        self.mouseDownLast = False

        self.posAtClick = None
        self.posAtRelease = None

    #Returns the control point's pos in format [posX, posY]
    def getPos(self):
        return self.posX, self.posY

    def move(self, newPos):
        self.posX = newPos[0]
        self.posY = newPos[1]

    #Calculates whether mouse is hovering, and whether user has selected point
    def update(self, mousePosX, mousePosY, zoom, screenWidth, screenHeight, screenBorder, pygame, offset, snap):
        zoomedSize = self.size / zoom
        self.mouseHovering = ((self.posX + (zoomedSize + 2) > mousePosX > self.posX - (zoomedSize + 2)) and
                               (self.posY + (zoomedSize + 2) > mousePosY > self.posY - (zoomedSize + 2)))

        if self.mouseHovering:
            self.size = self.baseSize + 2
        else:
            self.size = self.baseSize

        if not pygame.mouse.get_pressed()[0]:
            self.pointSelected = False
            self.new = False
            if self.posAtClick is not None:
                self.posAtRelease = self.getPos()

        if snap: roundValue = -1
        else: roundValue = 0

        if self.pointSelected:
            if (screenBorder - offset[0]) / zoom < mousePosX < (screenWidth - screenBorder - offset[0]) / zoom:
                self.posX = round(mousePosX, roundValue)

            if (screenBorder - offset[1]) / zoom < mousePosY < (screenHeight - screenBorder - offset[1]) / zoom:
                self.posY = round(mousePosY, roundValue)

        if not self.pointSelected:
            self.pointSelected = self.mouseHovering and pygame.mouse.get_pressed()[0] and not self.mouseDownLast

        if self.pointSelected and not self.mouseDownLast and not self.new:
            self.posAtClick = self.getPos()

        self.mouseDownLast = pygame.mouse.get_pressed()[0]

    #Draws point to screen
    def draw(self, colour, screen, pygame, offset, zoom):
        newPos = offsetPoints((self.posX, self.posY), offset, zoom, single = True)
        newPos = [int(point) for point in newPos]

        pygame.gfxdraw.aacircle(screen, newPos[0], newPos[1], self.size, colour)
        pygame.gfxdraw.filled_circle(screen, newPos[0], newPos[1], self.size, colour)

class Track:
    def __init__(self, resolution, points = None):
        if points is None:
            points = []

        self.points = points
        self.splinePoints = []
        self.history = History()

        self.mainPolyLeftEdge = []
        self.mainPolyRightEdge = []

        self.leftBorderInnerEdge = []
        self.leftBorderOuterEdge = []

        self.rightBorderInnerEdge = []
        self.rightBorderOuterEdge = []

        self.pointsSelected = []
        self.mouseHovering = None
        self.closed = False

        self.edit = True

        self.perSegRes = resolution
        self.scale = None
        self.length = None

        self.finishIndex = None
        self.finishDir = None

        self.width = 100

        for point in self.points:
            self.points.append(ControlPoint(point[0], point[1]))

        self.saved = True

    def clear(self):
        self.points = []
        self.splinePoints = []
        self.history = History()

        self.mainPolyLeftEdge = []
        self.mainPolyRightEdge = []

        self.leftBorderInnerEdge = []
        self.leftBorderOuterEdge = []

        self.rightBorderInnerEdge = []
        self.rightBorderOuterEdge = []

        self.width = 100

        self.scale = None
        self.length = None

        self.finishIndex = None
        self.finishDir = None

        self.closed = False
        self.saved = False

    def loadTrackPoints(self, pointCoords):
        self.clear()
        for point in pointCoords:
            self.add(ControlPoint(point[0], point[1]), update = False)

    def changeWidth(self, value):
        self.width = value
        self.computeTrackEdges()

        self.saved = False

    def changeWidthComplete(self, initialValue, slider):
        self.history.addAction("CHANGE WIDTH", [initialValue, self.width, slider])

    def changeRes(self, value):
        self.perSegRes = int(value)
        self.computeTrack()

        self.saved = False

    def changeResComplete(self, initialValue, slider):
        self.history.addAction("CHANGE RESOLUTION", [initialValue, self.perSegRes, slider])

    def calculateLength(self):
        if self.scale is not None:
            self.length = 0
            for point in range(len(self.splinePoints) - 1):
                self.length += pointDistance(self.splinePoints[point], self.splinePoints[point + 1]) * self.scale

    def updateCloseStatus(self, value, update = False):
        if self.closed is not value:
            self.closed = value
            if update:
                self.computeSpline(updatePoints = [0])
                self.computeTrackEdges(updatePoints = [0])

            self.saved = False

    #Checks if current mouse pos crosses the spline (for inserting points)
    def pointOnCurve(self, pointX, pointY, margin):
        smallestDistance = float('inf'), None
        segment = None
        nearestPointIndex = None

        for pointIndex in range(len(self.splinePoints) - 1):
            distanceToTrack, nearestPointOnTrack = lineToPointDistance(self.splinePoints[pointIndex], self.splinePoints[pointIndex + 1], (pointX, pointY))
            if distanceToTrack <= margin:
                if distanceToTrack < smallestDistance[0]:
                    smallestDistance = (distanceToTrack, nearestPointOnTrack)
                    nearestPointIndex = pointIndex
                    reconstructedT = (pointIndex / len(self.splinePoints))

                    numOfPoints = len(self.points) - 1
                    segment = int(reconstructedT * numOfPoints) + 1

        if segment is not None:
            return True, segment, smallestDistance[1], nearestPointIndex
        else:
            return False, None, None, None

    def add(self, anchorObject, index = -1, update = True, userPerformed = False):
        if index == -1:
            index = len(self.points)

        self.points.insert(index, anchorObject)
        if userPerformed:
            self.history.addAction("ADD POINT", [index, anchorObject])
        if len(self.points) > 1:
            if self.finishIndex is not None:
                if index <= self.finishIndex:
                    self.finishIndex += 1

            if index > 0:
                self.splinePoints = self.splinePoints[:((index - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.splinePoints[((index - 1) * self.perSegRes):]
                self.mainPolyLeftEdge = self.mainPolyLeftEdge[:((index - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.mainPolyLeftEdge[((index - 1) * self.perSegRes):]
                self.mainPolyRightEdge = self.mainPolyRightEdge[:((index - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.mainPolyRightEdge[((index - 1) * self.perSegRes):]

                self.leftBorderInnerEdge = self.leftBorderInnerEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.leftBorderInnerEdge[((index - 1) * self.perSegRes):]
                self.leftBorderOuterEdge = self.leftBorderOuterEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.leftBorderOuterEdge[((index - 1) * self.perSegRes):]

                self.rightBorderInnerEdge = self.rightBorderInnerEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.rightBorderInnerEdge[((index - 1) * self.perSegRes):]
                self.rightBorderOuterEdge = self.rightBorderOuterEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.rightBorderOuterEdge[((index - 1) * self.perSegRes):]

            else:
                self.splinePoints = ([''] * self.perSegRes) + self.splinePoints
                self.mainPolyLeftEdge = ([''] * self.perSegRes) + self.mainPolyLeftEdge
                self.mainPolyRightEdge = ([''] * self.perSegRes) + self.mainPolyRightEdge

                self.leftBorderInnerEdge = ([''] * self.perSegRes) + self.leftBorderInnerEdge
                self.leftBorderOuterEdge = ([''] * self.perSegRes) + self.leftBorderOuterEdge

                self.rightBorderInnerEdge = ([''] * self.perSegRes) + self.rightBorderInnerEdge
                self.rightBorderOuterEdge = ([''] * self.perSegRes) + self.rightBorderOuterEdge

        if update:
            self.computeSpline(updatePoints = [index])
            self.computeTrackEdges(updatePoints = [index])

        self.saved = False

    def remove(self, index = -1, update = True, userPerformed = False):
        if index == -1:
            index = len(self.points) - 1

        if len(self.points) - 1 >= index:
            removedPoint = self.points.pop(index)
            if userPerformed:
                self.history.addAction("REMOVE POINT", [index, removedPoint])

            if self.finishIndex is not None:
                if index <= self.finishIndex:
                    self.finishIndex -= 1

            if index > 0:
                self.splinePoints = self.splinePoints[:((index - 1) * self.perSegRes):] + self.splinePoints[(index * self.perSegRes):]
                self.mainPolyLeftEdge = self.mainPolyLeftEdge[:((index - 1) * self.perSegRes):] + self.mainPolyLeftEdge[(index * self.perSegRes):]
                self.mainPolyRightEdge = self.mainPolyRightEdge[:((index - 1) * self.perSegRes):] + self.mainPolyRightEdge[(index * self.perSegRes):]

                self.leftBorderInnerEdge = self.leftBorderInnerEdge[:((index - 1) * self.perSegRes)] + self.leftBorderInnerEdge[(index * self.perSegRes):]
                self.leftBorderOuterEdge = self.leftBorderOuterEdge[:((index - 1) * self.perSegRes)] + self.leftBorderOuterEdge[(index * self.perSegRes):]

                self.rightBorderInnerEdge = self.rightBorderInnerEdge[:((index - 1) * self.perSegRes)] + self.rightBorderInnerEdge[(index * self.perSegRes):]
                self.rightBorderOuterEdge = self.rightBorderOuterEdge[:((index - 1) * self.perSegRes)] + self.rightBorderOuterEdge[(index * self.perSegRes):]
            else:
                self.splinePoints = self.splinePoints[((index + 1) * self.perSegRes):]
                self.mainPolyLeftEdge = self.mainPolyLeftEdge[((index + 1) * self.perSegRes):]
                self.mainPolyRightEdge = self.mainPolyRightEdge[((index + 1) * self.perSegRes):]

                self.leftBorderInnerEdge = self.leftBorderInnerEdge[((index + 1) * self.perSegRes):]
                self.leftBorderOuterEdge = self.leftBorderOuterEdge[((index + 1) * self.perSegRes):]

                self.rightBorderInnerEdge = self.rightBorderInnerEdge[((index + 1) * self.perSegRes):]
                self.rightBorderOuterEdge = self.rightBorderOuterEdge[((index + 1) * self.perSegRes):]

            if update:
                self.computeTrack(updatePoints = [index])

            self.saved = False

    def undo(self):
        actions = self.history.undo()
        for action in actions:
            if action is not None:
                if action.command == "ADD POINT":
                    self.remove(action.params[0], update = False)
                    self.shouldTrackBeClosed()
                    self.computeTrack(updatePoints = [action.params[0]])
                elif action.command == "REMOVE POINT":
                    self.add(action.params[1], action.params[0])
                elif action.command == "MOVE POINT":
                    self.points[action.params[0]].move(action.params[1])
                    self.shouldTrackBeClosed()
                    self.computeTrack(updatePoints = [action.params[0]])
                elif action.command == "CHANGE WIDTH":
                    self.changeWidth(action.params[0])
                    action.params[2].updateValue(self.width)
                elif action.command == "CHANGE RESOLUTION":
                    self.changeRes(action.params[0])
                    action.params[2].updateValue(self.perSegRes)
                elif action.command == "SET SCALE":
                    self.scale = action.params[0]
                    self.calculateLength()
                elif action.command == "SET FINISH":
                    self.finishIndex = action.params[0][0]
                    self.finishDir = action.params[0][1]

    def redo(self):
        actions = self.history.redo()
        for action in actions:
            if action is not None:
                if action.command == "ADD POINT":
                    self.add(action.params[1], action.params[0], update = False)
                    self.shouldTrackBeClosed()
                    self.computeTrack(updatePoints = [action.params[0]])
                elif action.command == "REMOVE POINT":
                    self.remove(action.params[0])
                elif action.command == "MOVE POINT":
                    self.points[action.params[0]].move(action.params[2])
                    self.shouldTrackBeClosed()
                    self.computeTrack(updatePoints = [action.params[0]])
                elif action.command == "CHANGE WIDTH":
                    self.changeWidth(action.params[1])
                    action.params[2].updateValue(self.width)
                elif action.command == "CHANGE RESOLUTION":
                    self.changeRes(action.params[1])
                    action.params[2].updateValue(self.perSegRes)
                elif action.command == "SET SCALE":
                    self.scale = action.params[1]
                    self.calculateLength()
                elif action.command == "SET FINISH":
                    self.finishIndex = action.params[1][0]
                    self.finishDir = action.params[1][1]

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
                self.saved = False
                for tInt in range(*updateRange):
                    t = tInt / resolution
                    self.splinePoints[tInt] = (calculateSpline(self.returnPointCoords(), t))

            if self.closed:
                self.remove(0, False)
                self.remove(0, False)
                self.remove(-1, False)
                self.remove(-1, False)

            self.calculateLength()

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

                self.mainPolyLeftEdge = ([''] * resolution)
                self.mainPolyRightEdge = ([''] * resolution)

                self.leftBorderInnerEdge = ([''] * resolution)
                self.leftBorderOuterEdge = ([''] * resolution)

                self.rightBorderInnerEdge = ([''] * resolution)
                self.rightBorderOuterEdge = ([''] * resolution)

            for updateRange in updateRanges:
                self.saved = False
                for point in range(*updateRange):
                    self.mainPolyLeftEdge[point] = calculateSide(self.splinePoints, point, 5)
                    self.mainPolyRightEdge[point] = calculateSide(self.splinePoints, point, -5)

                    self.leftBorderInnerEdge[point] = calculateSide(self.splinePoints, point, self.width)
                    self.leftBorderOuterEdge[point] = calculateSide(self.splinePoints, point, self.width + 20)

                    self.rightBorderInnerEdge[point] = calculateSide(self.splinePoints, point, -self.width)
                    self.rightBorderOuterEdge[point] = calculateSide(self.splinePoints, point, -(self.width + 20))

    def computeTrack(self, updatePoints = []):
        self.computeSpline(updatePoints = updatePoints)
        self.computeTrackEdges(updatePoints = updatePoints)

    def computeCurbs(self, pygame, screen, offset, zoom):
        curbSpline = self.returnPointCoords()
        if self.closed:
            first1 = curbSpline[1]
            first2 = curbSpline[2]
            last1 = curbSpline[-2]
            last2 = curbSpline[-3]

            curbSpline.insert(0, last1)
            curbSpline.insert(0, last2)
            curbSpline.insert(-1, first1)
            curbSpline.insert(-1, first2)


        numOfSegments = len(self.points) - 1
        resolution = numOfSegments * 100
        for tInt in range(0, resolution):
            t = tInt / resolution
            curbSpline.append(calculateSpline(self.returnPointCoords(), t))

        if self.closed:
            curbSpline.pop(0)
            curbSpline.pop(0)
            curbSpline.pop(-1)
            curbSpline.pop(-1)

        curbThreshold = 0.02
        if len(self.points) >= 2:
            splinePoints = offsetPoints(curbSpline, offset, zoom)
            lengthOfSpline = len(splinePoints) - 1
            previousAngle = angle(splinePoints[0], splinePoints[1], splinePoints[2])
            curbRanges = []

            lowerBound = None
            upperBound = None

            for dot in range(1, lengthOfSpline):
                currentAngle = angle(splinePoints[dot - 1], splinePoints[dot], splinePoints[dot + 1])
                diffInAngle = abs(currentAngle - previousAngle)
                if diffInAngle > curbThreshold:
                    if lowerBound is None:
                        lowerBound = dot
                        upperBound = dot
                    else:
                        upperBound += 1
                elif upperBound is not None:
                    curbRanges.append((lowerBound, upperBound))

                    lowerBound = None
                    upperBound = None

                previousAngle = currentAngle

            if len(curbRanges) > 1:
                cleanedCurbRanges = []
                lowerBound = curbRanges[0][0]
                upperBound = curbRanges[0][1]
                minDotCount = 15
                for curbRange in range(1, len(curbRanges)):
                    if (pointDistance(splinePoints[curbRanges[curbRange][0]], splinePoints[upperBound]) / zoom) > 70:
                        if (upperBound - lowerBound) > minDotCount:
                            cleanedCurbRanges.append((lowerBound, upperBound))

                        lowerBound = curbRanges[curbRange][0]
                        upperBound = curbRanges[curbRange][1]
                    else:
                        upperBound = curbRanges[curbRange][1]

                if (upperBound - lowerBound) > minDotCount:
                    cleanedCurbRanges.append((lowerBound, upperBound))

                curbRanges = cleanedCurbRanges

            for curbRange in curbRanges:
                for dot in range(*curbRange):
                    pygame.draw.circle(screen, (252, 186, 3), splinePoints[dot], 5)

            self.saved = False

    def deKink(self):
        extendedSplinePoints = extendPointsBack(self.splinePoints)

        updateRange = (0, len(self.splinePoints))
        nonKinkCoordLeftInner = self.leftBorderInnerEdge[0]
        nonKinkCoordLeftOuter = self.leftBorderOuterEdge[0]

        nonKinkCoordRightInner = self.rightBorderInnerEdge[0]
        nonKinkCoordRightOuter = self.rightBorderOuterEdge[0]

        for seg in range(*updateRange):
            detectionRange = (max(seg - (2 * self.perSegRes), 0), min(seg + (2 * self.perSegRes), len(self.leftBorderInnerEdge)))
            if findKink(self.leftBorderInnerEdge[seg], extendedSplinePoints[detectionRange[0]: detectionRange[1]], self.width):
                self.leftBorderInnerEdge[seg] = nonKinkCoordLeftInner
                self.leftBorderOuterEdge[seg] = nonKinkCoordLeftOuter
            else:
                nonKinkCoordLeftInner = self.leftBorderInnerEdge[seg]
                nonKinkCoordLeftOuter = self.leftBorderOuterEdge[seg]

            if findKink(self.rightBorderInnerEdge[seg], extendedSplinePoints[detectionRange[0]: detectionRange[1]], self.width):
                self.rightBorderInnerEdge[seg] = nonKinkCoordRightInner
                self.rightBorderOuterEdge[seg] = nonKinkCoordRightOuter
            else:
                nonKinkCoordRightInner = self.rightBorderInnerEdge[seg]
                nonKinkCoordRightOuter = self.rightBorderOuterEdge[seg]

        self.saved = False

    def shouldTrackBeClosed(self):
        pointCoords = self.returnPointCoords()
        closedStatusBefore = self.closed
        if len(self.points) > 0:
            if pointCoords[0] == pointCoords[-1]:
                self.closed = True
                self.computeTrack(updatePoints = [0])
            else:
                closedBefore = self.closed
                self.closed = False
                if closedBefore:
                    self.computeTrack(updatePoints = [0, len(self.points) - 1])

        return [closedStatusBefore, self.closed]

    def update(self, mousePosX, mousePosY, zoom, screenWidth, screenHeight, screenBorder, pygame, offset, snap, screenRect):
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

        groupMove = False
        for pointIndex in range(len(self.points)):
            point = self.points[pointIndex]
            if screenRect.collidepoint(offsetPoints(point.getPos(), offset, zoom, True)):
                point.update(mousePosX, mousePosY, zoom, screenWidth, screenHeight, screenBorder, pygame, offset, snap)
                if (point.posAtClick is not None) and (point.posAtRelease is not None) and (point.posAtClick != point.posAtRelease):
                    self.history.addAction("MOVE POINT", [pointIndex, point.posAtClick, point.posAtRelease], group = groupMove)
                    groupMove = True
                    point.posAtClick = None
                    point.posAtRelease = None

        if len(self.points) >= 5:
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

        if len(self.pointsSelected) > 0 and self.edit:
            updatePoints = [point[1] for point in self.pointsSelected]

            self.computeSpline(updatePoints = updatePoints)
            self.computeTrackEdges(updatePoints = updatePoints)

    def findVisiblePoints(self, screenRect, offset, zoom):
        def isVisible(points):
            for seg in points:
                offsetSeg = offsetPoints(seg, offset, zoom, single = True)
                if screenRect.collidepoint(offsetSeg):
                    return True
            return False

        visiblePoints = []
        for point in range(len(self.points) - 1):
            pointVisible = True
            leftOuterVisibility = isVisible(self.leftBorderOuterEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1])
            if not leftOuterVisibility:
                rightOuterVisibility = isVisible(self.rightBorderOuterEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1])
                if not rightOuterVisibility:
                    pointVisible = False

            if pointVisible:
                visiblePoints.append(point)
        return visiblePoints

    def draw(self, programColours, screen, pygame, offset, zoom, switchFront, screenRect, viewMode):
        if len(self.points) >= 2:
            visiblePoints = self.findVisiblePoints(screenRect, offset, zoom)
            for point in range(len(self.points) - 1):
                if point in visiblePoints:
                    if viewMode == "Track" or viewMode == "Skeleton":
                        leftBorderInnerEdgeSegment = offsetPoints(self.leftBorderInnerEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1], offset, zoom)
                        leftBorderOuterEdgeSegment = offsetPoints(self.leftBorderOuterEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1], offset, zoom)

                        rightBorderInnerEdgeSegment = offsetPoints(self.rightBorderInnerEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1], offset, zoom)
                        rightBorderOuterEdgeSegment = offsetPoints(self.rightBorderOuterEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1], offset, zoom)

                        if (point == len(self.points) - 2) and self.closed:
                            leftBorderInnerEdgeSegment.append(offsetPoints(self.leftBorderInnerEdge[0], offset, zoom, single = True))
                            leftBorderOuterEdgeSegment.append(offsetPoints(self.leftBorderOuterEdge[0], offset, zoom, single = True))

                            rightBorderInnerEdgeSegment.append(offsetPoints(self.rightBorderInnerEdge[0], offset, zoom, single = True))
                            rightBorderOuterEdgeSegment.append(offsetPoints(self.rightBorderOuterEdge[0], offset, zoom, single = True))

                        leftTrackEdgePolygon = formPolygon(leftBorderInnerEdgeSegment, leftBorderOuterEdgeSegment)
                        rightTrackEdgePolygon = formPolygon(rightBorderInnerEdgeSegment, rightBorderOuterEdgeSegment)

                        pygame.gfxdraw.aapolygon(screen, leftTrackEdgePolygon, programColours["white"])
                        pygame.gfxdraw.filled_polygon(screen, leftTrackEdgePolygon, programColours["white"])

                        pygame.gfxdraw.aapolygon(screen, rightTrackEdgePolygon, programColours["white"])
                        pygame.gfxdraw.filled_polygon(screen, rightTrackEdgePolygon, programColours["white"])

            for point in range(len(self.points) - 1):
                if point in visiblePoints:
                    if viewMode == "Track":
                        leftBorderInnerEdgeSegment = offsetPoints(self.leftBorderInnerEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1], offset, zoom)
                        rightBorderInnerEdgeSegment = offsetPoints(self.rightBorderInnerEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1], offset, zoom)

                        if (point == len(self.points) - 2) and self.closed:
                            leftBorderInnerEdgeSegment.append(offsetPoints(self.leftBorderInnerEdge[0], offset, zoom, single = True))
                            rightBorderInnerEdgeSegment.append(offsetPoints(self.rightBorderInnerEdge[0], offset, zoom, single = True))

                        mainTrackPolygon = formPolygon(leftBorderInnerEdgeSegment, rightBorderInnerEdgeSegment)

                        pygame.gfxdraw.aapolygon(screen, mainTrackPolygon, programColours["mainTrack"])
                        pygame.gfxdraw.filled_polygon(screen, mainTrackPolygon, programColours["mainTrack"])

            if self.edit or viewMode == "Curve":
                for point in range(len(self.points) - 1):
                    if point in visiblePoints:
                        if viewMode == "Track" or viewMode == "Skeleton" or viewMode == "Curve":
                            mainPolyLeftEdgeSegment = offsetPoints(self.mainPolyLeftEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1], offset, zoom)
                            mainPolyRightEdgeSegment = offsetPoints(self.mainPolyRightEdge[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1], offset, zoom)

                            if (point == len(self.points) - 2) and self.closed:
                                mainPolyLeftEdgeSegment.append(offsetPoints(self.mainPolyLeftEdge[0], offset, zoom, single = True))
                                mainPolyRightEdgeSegment.append(offsetPoints(self.mainPolyRightEdge[0], offset, zoom, single = True))

                            mainCurvePolygon = formPolygon(mainPolyLeftEdgeSegment, mainPolyRightEdgeSegment)

                            pygame.gfxdraw.aapolygon(screen, mainCurvePolygon, programColours["curve"])
                            pygame.gfxdraw.filled_polygon(screen, mainCurvePolygon, programColours["curve"])

            for point in range(len(self.points) - 1):
                if point in visiblePoints:
                    if viewMode == "Spline Dots":
                        centreCurveDots = offsetPoints(self.splinePoints[(point * self.perSegRes):((point + 1) * self.perSegRes) + 1], offset, zoom)
                        for dot in centreCurveDots:
                            pygame.gfxdraw.aacircle(screen, int(dot[0]), int(dot[1]), 5, programColours["curve"])
                            pygame.gfxdraw.filled_circle(screen, int(dot[0]), int(dot[1]), 5, programColours["curve"])

        if self.edit:
            for pointIndex in range(len(self.points)):
                point = self.points[pointIndex]

                if screenRect.collidepoint(offsetPoints(point.getPos(), offset, zoom, True)):
                    if (not switchFront and pointIndex == len(self.points) - 1) or (switchFront and pointIndex == 0) or (self.closed and ((pointIndex == 0) or (pointIndex == len(self.points) - 1))):
                        colour = programColours["frontControlPoint"]
                    else:
                        colour = programColours["controlPoint"]

                    point.draw(colour, screen, pygame, offset, zoom)
