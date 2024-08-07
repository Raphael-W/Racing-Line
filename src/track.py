from utils import *
from history import *

import base64

#Checks if point on track gets closer to the centre than it should (indicating a kink)
def isPointKinked(point, linePoints, width):
    width = width / 2

    for pointIndex in range(len(linePoints)):
        if pointDistance(point, linePoints[pointIndex]) < (width - 1): return True

    return False

#Main mathematical formula for track curve
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

class ControlPoint:
    def __init__(self, posX, posY):
        self.posX = posX
        self.posY = posY

        self.baseSize = 10
        self.size = self.baseSize

        self.new = True
        self.pointSelected = True
        self.mouseHovering = False
        self.mouseDownLast = False

        self.posAtClick = None
        self.posAtRelease = None

    #Returns the control point's pos in format [posX, posY]
    def getPos(self):
        return self.posX, self.posY

    #Move a control point to a specific location
    def move(self, newPos):
        self.posX = newPos[0]
        self.posY = newPos[1]

    #Calculates whether mouse is hovering, and whether user has selected point
    def update(self, mousePosX, mousePosY, zoom, screenWidth, screenHeight, screenBorder, pygame, offset):
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

        if self.pointSelected:
            if (screenBorder - offset[0]) / zoom < mousePosX < (screenWidth - screenBorder - offset[0]) / zoom:
                self.posX = mousePosX

            if (screenBorder - offset[1]) / zoom < mousePosY < (screenHeight - screenBorder - offset[1]) / zoom:
                self.posY = mousePosY

        if not self.pointSelected:
            self.pointSelected = (self.mouseHovering and pygame.mouse.get_pressed()[0] and not self.mouseDownLast)

        if self.pointSelected and not self.mouseDownLast and not self.new:
            self.posAtClick = self.getPos()

        self.mouseDownLast = pygame.mouse.get_pressed()[0]

    #Draws point to screen
    def draw(self, colour, screen, pygame, offset, zoom):
        newPos = offsetPoints((self.posX, self.posY), offset, zoom, single = True)
        newPos = [int(point) for point in newPos]

        if checkIfOnscreen(newPos, screen.get_size()):
            pygame.gfxdraw.aacircle(screen, newPos[0], newPos[1], self.size, colour)
            pygame.gfxdraw.filled_circle(screen, newPos[0], newPos[1], self.size, colour)

class Track:
    def __init__(self, resolution, points = None):
        if points is None:
            points = []

        self.points = points
        self.splinePoints = []

        #Visual Track Points
        self.__mainPolyLeftEdge = []
        self.__mainPolyRightEdge = []

        self.__leftBorderInnerEdge = []
        self.__leftBorderOuterEdge = []

        self.__rightBorderInnerEdge = []
        self.__rightBorderOuterEdge = []

        #Cached, offset - Visual Track Points
        self.__offset_mainPolyLeftEdge = []
        self.__offset_mainPolyRightEdge = []

        self.__offset_leftBorderInnerEdge = []
        self.__offset_leftBorderOuterEdge = []

        self.__offset_rightBorderInnerEdge = []
        self.__offset_rightBorderOuterEdge = []

        self.__offset_splinePoints = []

        self.offsetValue = (0, 0)
        self.zoomValue = 1

        self.pointsSelected = []
        self.mouseHovering = None
        self.closed = False

        self.perSegRes = resolution
        self.scale = 0.2

        self.length = 0

        self.finishIndex = None
        self.finishDir = True

        self.referenceImageDir = None

        self.width = 12

        for point in self.points:
            self.points.append(ControlPoint(point[0], point[1]))

        self.history = History(self)

    #Clear track, and any settings
    def clear(self):
        self.points = []
        self.splinePoints = []
        self.history = History(self)

        #Visual Track Points
        self.__mainPolyLeftEdge = []
        self.__mainPolyRightEdge = []

        self.__leftBorderInnerEdge = []
        self.__leftBorderOuterEdge = []

        self.__rightBorderInnerEdge = []
        self.__rightBorderOuterEdge = []

        #Cached, offset - Visual Track Points
        self.__offset_mainPolyLeftEdge = []
        self.__offset_mainPolyRightEdge = []

        self.__offset_leftBorderInnerEdge = []
        self.__offset_leftBorderOuterEdge = []

        self.__offset_rightBorderInnerEdge = []
        self.__offset_rightBorderOuterEdge = []

        self.__offset_splinePoints = []

        self.width = 12

        self.scale = 0.2
        self.length = 0

        self.finishIndex = None
        self.finishDir = None

        self.referenceImageDir = None

        self.closed = False

    #Called when opening tracks from a save file, and is used to load in the track and its data
    def loadTrackPoints(self, pointCoords):
        self.clear()
        for point in pointCoords:
            self.add(ControlPoint(point[0], point[1]), update = False)

    #Collects relevant data about track and combines it into a dictionary used for saving
    def getSaveState(self):
        referenceImageData = None
        if self.referenceImageDir is not None:
            with open(self.referenceImageDir, "rb") as img_file:
                referenceImageData = base64.b64encode(img_file.read()).decode('utf-8')

        points = self.returnPointCoords()
        properties = {"width"      : self.width,
                      "trackRes"   : self.perSegRes,
                      "closed"     : self.closed,
                      "finishIndex": self.finishIndex,
                      "finishDir"  : self.finishDir,
                      "referenceImage": referenceImageData}

        return {"points"    : points,
                "properties": properties}

    #Used to check whether the track has been changed
    def getEdgePoints(self):
        return [list(self.__leftBorderInnerEdge), self.__rightBorderInnerEdge]

    #Returns coordinates of start line
    def getStartPos(self):
        if self.finishIndex is None:
            finishIndex = 0.1
            finishDir = True
        else:
            finishIndex = self.finishIndex
            finishDir = self.finishDir

        finishCoord = self.splinePoints[int(finishIndex * self.perSegRes)]
        finishNeighbourCoord = self.splinePoints[int(finishIndex * self.perSegRes) + 1]

        trackAngle = 0 + math.degrees(math.atan2(finishCoord[0] - finishNeighbourCoord[0], (finishCoord[1] - finishNeighbourCoord[1]))) - 90
        startAngle = trackAngle + (finishDir * 180)

        return self.splinePoints[int(finishIndex * self.perSegRes)], startAngle

    def save(self):
        self.history.saveTrack()

    def isSaved(self):
        return self.history.saved

    def changeWidth(self, value):
        self.width = value
        self.computeTrackEdges()

    #Called when user stops setting width (lets go of track width slider)
    def changeWidthComplete(self, initialValue, slider):
        self.history.addAction("CHANGE WIDTH", [initialValue, self.width, slider])

    def changeRes(self, value):
        self.perSegRes = int(value)
        self.computeTrack()

    #Called when user stops setting track res (lets go of track resolution slider)
    def changeResComplete(self, initialValue, slider):
        self.history.addAction("CHANGE RESOLUTION", [initialValue, self.perSegRes, slider])

    #Calculates length of track by adding length of each segment
    def calculateLength(self):
        if self.scale is not None:
            self.length = 0
            for point in range(len(self.splinePoints) - 1):
                self.length += pointDistance(self.splinePoints[point], self.splinePoints[point + 1]) * self.scale

    #Multiplies each point by scale factor
    def scalePoints(self, scale):
        for point in self.points:
            newPosition = (point.posX * scale, point.posY * scale)
            point.move(newPosition)
        self.computeTrack()

    def updateCloseStatus(self, value, update = False):
        if self.closed is not value:
            self.closed = value
            if update:
                self.computeSpline(updatePoints = [0])
                self.computeTrackEdges(updatePoints = [0])

    #Called in game loop
    def updateOffsetValues(self, offset, zoom):
        offsetChanged = False
        if (offset != self.offsetValue) or (zoom != self.zoomValue):
            offsetChanged = True

        self.offsetValue = offset
        self.zoomValue = zoom

        if offsetChanged:
            self.offsetTrackEdges()

    #Offsets each point that makes up track edges by current values for offset and zoom
    def offsetTrackEdges(self, updatePoints = [], updateRange = []):
        self.__offset_mainPolyLeftEdge = offsetPoints(self.__mainPolyLeftEdge, self.offsetValue, self.zoomValue)
        self.__offset_mainPolyRightEdge = offsetPoints(self.__mainPolyRightEdge, self.offsetValue, self.zoomValue)

        self.__offset_leftBorderInnerEdge = offsetPoints(self.__leftBorderInnerEdge, self.offsetValue, self.zoomValue)
        self.__offset_leftBorderOuterEdge = offsetPoints(self.__leftBorderOuterEdge, self.offsetValue, self.zoomValue)

        self.__offset_rightBorderInnerEdge = offsetPoints(self.__rightBorderInnerEdge, self.offsetValue, self.zoomValue)
        self.__offset_rightBorderOuterEdge = offsetPoints(self.__rightBorderOuterEdge, self.offsetValue, self.zoomValue)

        self.__offset_splinePoints = offsetPoints(self.splinePoints, self.offsetValue, self.zoomValue)

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

    #Adds new control point
    def add(self, controlPoint, index = -1, update = True, userPerformed = False):
        if index == -1:
            index = len(self.points)

        self.points.insert(index, controlPoint)
        if userPerformed:
            self.history.addAction("ADD POINT", [index, controlPoint])
        if len(self.points) > 1:
            if self.finishIndex is not None:
                if index <= self.finishIndex:
                    self.finishIndex += 1

            if index > 0:
                self.splinePoints = self.splinePoints[:((index - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.splinePoints[((index - 1) * self.perSegRes):]

                self.__mainPolyLeftEdge = self.__offset_mainPolyLeftEdge = self.__mainPolyLeftEdge[:((index - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.__mainPolyLeftEdge[((index - 1) * self.perSegRes):]
                self.__mainPolyRightEdge = self.__offset_mainPolyRightEdge = self.__mainPolyRightEdge[:((index - 1) * self.perSegRes):] + ([''] * self.perSegRes) + self.__mainPolyRightEdge[((index - 1) * self.perSegRes):]

                self.__leftBorderInnerEdge = self.__offset_leftBorderInnerEdge = self.__leftBorderInnerEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.__leftBorderInnerEdge[((index - 1) * self.perSegRes):]
                self.__leftBorderOuterEdge = self.__offset_leftBorderOuterEdge = self.__leftBorderOuterEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.__leftBorderOuterEdge[((index - 1) * self.perSegRes):]

                self.__rightBorderInnerEdge = self.__offset_rightBorderInnerEdge = self.__rightBorderInnerEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.__rightBorderInnerEdge[((index - 1) * self.perSegRes):]
                self.__rightBorderOuterEdge = self.__offset_rightBorderOuterEdge = self.__rightBorderOuterEdge[:((index - 1) * self.perSegRes)] + ([''] * self.perSegRes) + self.__rightBorderOuterEdge[((index - 1) * self.perSegRes):]

            else:
                self.splinePoints = ([''] * self.perSegRes) + self.splinePoints

                self.__mainPolyLeftEdge = self.__offset_mainPolyLeftEdge = ([''] * self.perSegRes) + self.__mainPolyLeftEdge
                self.__mainPolyRightEdge = self.__offset_mainPolyRightEdge = ([''] * self.perSegRes) + self.__mainPolyRightEdge

                self.__leftBorderInnerEdge = self.__offset_leftBorderInnerEdge = ([''] * self.perSegRes) + self.__leftBorderInnerEdge
                self.__leftBorderOuterEdge = self.__offset_leftBorderOuterEdge = ([''] * self.perSegRes) + self.__leftBorderOuterEdge

                self.__rightBorderInnerEdge = self.__offset_rightBorderInnerEdge = ([''] * self.perSegRes) + self.__rightBorderInnerEdge
                self.__rightBorderOuterEdge = self.__offset_rightBorderOuterEdge = ([''] * self.perSegRes) + self.__rightBorderOuterEdge

        if update:
            self.computeTrack(updatePoints = [index])

    #Removes control point at index specified
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

                self.__mainPolyLeftEdge = self.__offset_mainPolyLeftEdge = self.__mainPolyLeftEdge[:((index - 1) * self.perSegRes):] + self.__mainPolyLeftEdge[(index * self.perSegRes):]
                self.__mainPolyRightEdge = self.__offset_mainPolyRightEdge = self.__mainPolyRightEdge[:((index - 1) * self.perSegRes):] + self.__mainPolyRightEdge[(index * self.perSegRes):]

                self.__leftBorderInnerEdge = self.__offset_leftBorderInnerEdge = self.__leftBorderInnerEdge[:((index - 1) * self.perSegRes)] + self.__leftBorderInnerEdge[(index * self.perSegRes):]
                self.__leftBorderOuterEdge = self.__offset_leftBorderOuterEdge = self.__leftBorderOuterEdge[:((index - 1) * self.perSegRes)] + self.__leftBorderOuterEdge[(index * self.perSegRes):]

                self.__rightBorderInnerEdge = self.__offset_rightBorderInnerEdge = self.__rightBorderInnerEdge[:((index - 1) * self.perSegRes)] + self.__rightBorderInnerEdge[(index * self.perSegRes):]
                self.__rightBorderOuterEdge = self.__offset_rightBorderOuterEdge = self.__rightBorderOuterEdge[:((index - 1) * self.perSegRes)] + self.__rightBorderOuterEdge[(index * self.perSegRes):]

            else:
                self.splinePoints = self.splinePoints[((index + 1) * self.perSegRes):]

                self.__mainPolyLeftEdge = self.__offset_mainPolyLeftEdge = self.__mainPolyLeftEdge[((index + 1) * self.perSegRes):]
                self.__mainPolyRightEdge = self.__offset_mainPolyRightEdge = self.__mainPolyRightEdge[((index + 1) * self.perSegRes):]

                self.__leftBorderInnerEdge = self.__offset_leftBorderInnerEdge = self.__leftBorderInnerEdge[((index + 1) * self.perSegRes):]
                self.__leftBorderOuterEdge = self.__offset_leftBorderOuterEdge = self.__leftBorderOuterEdge[((index + 1) * self.perSegRes):]

                self.__rightBorderInnerEdge = self.__offset_rightBorderInnerEdge = self.__rightBorderInnerEdge[((index + 1) * self.perSegRes):]
                self.__rightBorderOuterEdge = self.__offset_rightBorderOuterEdge = self.__rightBorderOuterEdge[((index + 1) * self.perSegRes):]

            if update:
                self.computeTrack(updatePoints = [index])

    #Handles undoing of track actions (control point moving, width changes etc.)
    def undo(self, actions):
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
                    self.scalePoints(1 / (action.params[0] * (1 / self.scale)))
                    self.calculateLength()
                elif action.command == "SET FINISH":
                    self.finishIndex = action.params[0][0]
                    self.finishDir = action.params[0][1]
        self.history.checkIfSaved()
        return actions

    #Handles redoing of previously undone actions
    def redo(self, actions):
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
                    self.scalePoints(action.params[0] * (1 / self.scale))
                    self.calculateLength()
                elif action.command == "SET FINISH":
                    self.finishIndex = action.params[1][0]
                    self.finishDir = action.params[1][1]
        self.history.checkIfSaved()
        return actions

    def returnPointCoords(self):
        pointCoords = []
        for point in self.points:
            pointCoords.append(point.getPos())

        return pointCoords

    #Updates segments that make up main track curve. If no points are specified, whole track curve is updated
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

            self.calculateLength()

    #Updates segments that make up visual track. If no points are specified, whole track is updated
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

                self.__mainPolyLeftEdge = self.__offset_mainPolyLeftEdge = ([''] * resolution)
                self.__mainPolyRightEdge = self.__offset_mainPolyRightEdge = ([''] * resolution)

                self.__leftBorderInnerEdge = self.__offset_leftBorderInnerEdge = ([''] * resolution)
                self.__leftBorderOuterEdge = self.__offset_leftBorderOuterEdge = ([''] * resolution)

                self.__rightBorderInnerEdge = self.__offset_rightBorderInnerEdge = ([''] * resolution)
                self.__rightBorderOuterEdge = self.__offset_rightBorderOuterEdge = ([''] * resolution)

            for updateRange in updateRanges:
                for point in range(*updateRange):
                    self.__mainPolyLeftEdge[point] = self.__offset_mainPolyLeftEdge[point] = calculateSide(self.splinePoints, point, 5)
                    self.__mainPolyRightEdge[point] = self.__offset_mainPolyRightEdge[point] = calculateSide(self.splinePoints, point, -5)

                    self.__leftBorderInnerEdge[point] = self.__offset_leftBorderInnerEdge[point] = calculateSide(self.splinePoints, point, (self.width * 5))
                    self.__leftBorderOuterEdge[point] = self.__offset_leftBorderOuterEdge[point] = calculateSide(self.splinePoints, point, (self.width * 5) + 7)

                    self.__rightBorderInnerEdge[point] = self.__offset_rightBorderInnerEdge[point] = calculateSide(self.splinePoints, point, -(self.width * 5))
                    self.__rightBorderOuterEdge[point] = self.__offset_rightBorderOuterEdge[point] = calculateSide(self.splinePoints, point, -((self.width * 5) + 7))


            self.offsetTrackEdges()

    #Runs both computeSpline() and computeTrackEdges()
    def computeTrack(self, updatePoints = []):
        self.computeSpline(updatePoints = updatePoints)
        self.computeTrackEdges(updatePoints = updatePoints)

    #UNFINISHED - Used to find where curbs should be drawn
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

    #Loops over every point finding where a kink starts and ends, before removing it
    def deKink(self):
        extendedSplinePoints = extendPoints(self.splinePoints)

        updateRange = (1, len(self.splinePoints))
        nonKinkCoordLeftInner = self.__leftBorderInnerEdge[0]
        nonKinkCoordLeftOuter = self.__leftBorderOuterEdge[0]

        nonKinkCoordRightInner = self.__rightBorderInnerEdge[0]
        nonKinkCoordRightOuter = self.__rightBorderOuterEdge[0]

        for seg in range(*updateRange):
            detectionRange = (max(seg - (2 * self.perSegRes), 0), min(seg + (2 * self.perSegRes), len(self.__leftBorderInnerEdge)))
            if isPointKinked(self.__leftBorderInnerEdge[seg], extendedSplinePoints[detectionRange[0]: detectionRange[1]], (self.width * (1 / self.scale))):
                self.__leftBorderInnerEdge[seg] = nonKinkCoordLeftInner
                self.__leftBorderOuterEdge[seg] = nonKinkCoordLeftOuter
            else:
                nonKinkCoordLeftInner = self.__leftBorderInnerEdge[seg]
                nonKinkCoordLeftOuter = self.__leftBorderOuterEdge[seg]

            if isPointKinked(self.__rightBorderInnerEdge[seg], extendedSplinePoints[detectionRange[0]: detectionRange[1]], (self.width * (1 / self.scale))):
                self.__rightBorderInnerEdge[seg] = nonKinkCoordRightInner
                self.__rightBorderOuterEdge[seg] = nonKinkCoordRightOuter
            else:
                nonKinkCoordRightInner = self.__rightBorderInnerEdge[seg]
                nonKinkCoordRightOuter = self.__rightBorderOuterEdge[seg]

        self.offsetTrackEdges()

    #Checks whether track should be closed based off of whether end and start points are at the same positions
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

    def update(self, mousePosX, mousePosY, zoom, screenWidth, screenHeight, screenBorder, pygame, offset, screenRect, directories):
        self.pointsSelected = [[self.points[point], point] for point in range(len(self.points)) if self.points[point].pointSelected]

        #If track is closed, then moving join will select both points. This unselects one of the points
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

        #Handles when control point movements begins and ends
        groupMove = False
        for pointIndex in range(len(self.points)):
            point = self.points[pointIndex]
            if screenRect.collidepoint(offsetPoints(point.getPos(), offset, zoom, True)):
                point.update(mousePosX, mousePosY, zoom, screenWidth, screenHeight, screenBorder, pygame, offset)
                if (point.posAtClick is not None) and (point.posAtRelease is not None) and (point.posAtClick != point.posAtRelease):
                    self.history.addAction("MOVE POINT", [pointIndex, point.posAtClick, point.posAtRelease], group = groupMove)
                    groupMove = True
                    point.posAtClick = None
                    point.posAtRelease = None

        #Handles when the end control point and start control point should connect
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

        #Updates track
        if len(self.pointsSelected) > 0:
            updatePoints = [point[1] for point in self.pointsSelected]

            self.computeSpline(updatePoints = updatePoints)
            self.computeTrackEdges(updatePoints = updatePoints)

    #Main rendering algorithm for drawing track
    def draw(self, programColours, screen, pygame, switchFront, viewMode, antialiasing):
        if len(self.points) >= 2:
            if viewMode in ["Track", "Skeleton", "Display"]:
                for point in range(len(self.points) - 1):
                    pass
                    leftTrackEdgePolygon = formPolygon(self.__offset_leftBorderInnerEdge, self.__offset_leftBorderOuterEdge, slice((point * self.perSegRes), ((point + 1) * self.perSegRes) + 1), ((point == len(self.points) - 2) and self.closed))
                    rightTrackEdgePolygon = formPolygon(self.__offset_rightBorderInnerEdge, self.__offset_rightBorderOuterEdge, slice((point * self.perSegRes), ((point + 1) * self.perSegRes) + 1), ((point == len(self.points) - 2) and self.closed))

                    if antialiasing:
                        pygame.gfxdraw.aapolygon(screen, leftTrackEdgePolygon, programColours["white"])
                    pygame.gfxdraw.filled_polygon(screen, leftTrackEdgePolygon, programColours["white"])

                    if antialiasing:
                        pygame.gfxdraw.aapolygon(screen, rightTrackEdgePolygon, programColours["white"])
                    pygame.gfxdraw.filled_polygon(screen, rightTrackEdgePolygon, programColours["white"])

            if viewMode in ["Track", "Display"]:
                for point in range(len(self.points) - 1):
                    mainTrackPolygon = formPolygon(self.__offset_leftBorderInnerEdge, self.__offset_rightBorderInnerEdge, slice((point * self.perSegRes), ((point + 1) * self.perSegRes) + 1), ((point == len(self.points) - 2) and self.closed))

                    if antialiasing:
                        pygame.gfxdraw.aapolygon(screen, mainTrackPolygon, programColours["mainTrack"])
                    pygame.gfxdraw.filled_polygon(screen, mainTrackPolygon, programColours["mainTrack"])

            if viewMode in ["Track", "Skeleton", "Curve"]:
                for point in range(len(self.points) - 1):
                    mainCurvePolygon = formPolygon(self.__offset_mainPolyLeftEdge, self.__offset_mainPolyRightEdge, slice((point * self.perSegRes), ((point + 1) * self.perSegRes) + 1), ((point == len(self.points) - 2) and self.closed))

                    if antialiasing:
                        pygame.gfxdraw.aapolygon(screen, mainCurvePolygon, programColours["curve"])
                    pygame.gfxdraw.filled_polygon(screen, mainCurvePolygon, programColours["curve"])

            if viewMode in ["Spline Dots"]:
                for dot in self.__offset_splinePoints:
                    if antialiasing:
                        pygame.gfxdraw.aacircle(screen, int(dot[0]), int(dot[1]), 4, programColours["curve"])
                    pygame.gfxdraw.filled_circle(screen, int(dot[0]), int(dot[1]), 4, programColours["curve"])

        if viewMode in ["Track", "Skeleton", "Curve", "Spline Dots"]:
            for pointIndex in range(len(self.points)):
                point = self.points[pointIndex]

                if (not switchFront and pointIndex == len(self.points) - 1) or (switchFront and pointIndex == 0) or (self.closed and ((pointIndex == 0) or (pointIndex == len(self.points) - 1))):
                    colour = programColours["frontControlPoint"]
                else:
                    colour = programColours["controlPoint"]

                point.draw(colour, screen, pygame, self.offsetValue, self.zoomValue)

        if self.finishIndex is not None and viewMode in ["Display"]:
            checkeredHeight = (12 * self.zoomValue)
            checkeredWidthCount = int((self.width * (1 / self.scale) * self.zoomValue) // checkeredHeight)
            checkeredWidth = checkeredHeight + (((self.width * self.scale * self.zoomValue) % checkeredHeight) / checkeredWidthCount)

            finishIndex = int(self.finishIndex * self.perSegRes)
            finishAngle = self.getStartPos()[1]

            if self.finishDir:
                startLeftCoord = int(self.__offset_leftBorderInnerEdge[finishIndex][0]), int(self.__offset_leftBorderInnerEdge[finishIndex][1])
            else:
                startLeftCoord = int(self.__offset_rightBorderInnerEdge[finishIndex][0]), int(self.__offset_rightBorderInnerEdge[finishIndex][1])

            for y in range(4):
                for x in range(checkeredWidthCount):
                    topLeft = startLeftCoord[0] - (cosDeg(finishAngle) * (checkeredHeight * y)) - (sinDeg(finishAngle) * (checkeredWidth * x)), startLeftCoord[1] + (sinDeg(finishAngle) * (checkeredHeight * y)) - (cosDeg(finishAngle) * (checkeredWidth * x))

                    corner1 = topLeft
                    corner2 = topLeft[0] - (cosDeg(finishAngle) * checkeredHeight), topLeft[1] + (sinDeg(finishAngle) * checkeredHeight)
                    corner3 = topLeft[0] - (cosDeg(finishAngle) * checkeredHeight) - (sinDeg(finishAngle) * checkeredWidth), topLeft[1] + (sinDeg(finishAngle) * checkeredHeight) - (cosDeg(finishAngle) * checkeredWidth)
                    corner4 = topLeft[0] - (sinDeg(finishAngle) * checkeredWidth), topLeft[1] - (cosDeg(finishAngle) * checkeredWidth)

                    if (x + y) % 2 == 0:
                        checkeredColour = (0, 0, 0)
                    else:
                        checkeredColour = (200, 200, 200)

                    checkeredSquarePoints = [corner1, corner2, corner3, corner4]
                    pygame.draw.polygon(screen, checkeredColour, checkeredSquarePoints)
