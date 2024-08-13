import math
import numpy as np

#Calculates distance between 2 points
def pointDistance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    return math.sqrt(((y2 - y1) ** 2) + ((x1 - x2) ** 2))

#Calculate gradient of line, formed by 2 points
def gradient(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    if (x2 - x1) == 0:
        return 0
    return (y2 - y1) / (x2 - x1)

#Calculate the angle between 3 points
def angle(point1, point2, point3):
    distance12 = pointDistance(point1, point2) #
    distance23 = pointDistance(point2, point3)
    distance31 = pointDistance(point3, point1)

    cosAngle = ((distance12 ** 2) + (distance23 ** 2) - (distance31 ** 2)) / (2 * distance12 * distance23)
    cosAngle = max(min(cosAngle, 1), -1)
    angleRad = math.acos(cosAngle)
    angleDegrees = angleRad * (180.0 / math.pi)

    return angleDegrees

def bearing(pos1, pos2):
    tempPos1 = pos1
    pos1 = pos2
    pos2 = tempPos1
    changeX = pos2[0] - pos1[0]
    changeY = pos2[1] - pos1[1]

    bearingAngle = math.atan2(changeX, changeY)
    bearingAngle = math.degrees(bearingAngle)
    return bearingAngle % 360

def makeAnglePositive(angle):
    return angle % 360

def sameSign(nums):
    return all([x > 0 for x in nums]) or all([x < 0 for x in nums])

#Finds the shortest distance between a point and a line
def lineToPointDistance(lineA, lineB, point):
    lineA = np.array(lineA)
    lineB = np.array(lineB)
    point = np.array(point)

    l2 = pointDistance(lineA, lineB) ** 2
    if l2 == 0:
        return pointDistance(point, lineA)

    t = max(0, min(1, np.dot(point - lineA, lineB - lineA) / l2))
    projection = lineA + t * (lineB - lineA)
    return pointDistance(point, projection), projection

def makeInfiniteLine(pointA, pointB):
    grad = gradient(pointA, pointB)
    intercept = pointA[1] - (grad * pointA[0])

    return grad, intercept

#Calculate intersection point of an infinitely long line (y = mx + c) and a line segment
def lineSegmentIntersection(pointA, pointB, m, c, facing, start):
    segM, segC = makeInfiniteLine(pointA, pointB)
    if segM == m:
        return None

    intersection = infiniteLineIntersection(segM, segC, m, c)
    onSegment = pointLiesOnSegment(intersection, pointA, pointB)
    direction = bearing(start, intersection) - 90
    facing = makeAnglePositive(360 - facing)
    correctDirection = ((int(direction + facing) % 360) == 0) or ((int(direction + facing + 1) % 360) == 0) or ((int(direction + facing - 1) % 360) == 0)
    if onSegment and correctDirection:
        return intersection
    else:
        return None

def infiniteLineIntersection(line1M, line1C, line2M, line2C):
    if line1M == line2M:
        return None

    x = (line1C - line2C) / (line2M - line1M)
    y = line1M * x + line1C

    return x, y

def pointLiesOnSegment(point, lineA, lineB):
    distPointToA = pointDistance(point, lineA)
    distPointToB = pointDistance(point, lineB)
    lineLength = pointDistance(lineA, lineB)
    tolerance = 0.00001

    return (lineLength - tolerance) <= (distPointToA + distPointToB) <=  (lineLength + tolerance)

#Extends a list of points back by taking the length and gradient of the last segment and inserting it at the end
def extendPointsBack(points):
    xExtBack= (points[-1][0] - points[-2][0])
    yExtBack = (points[-1][1] - points[-2][1])
    pointExtBack = (points[-1][0] + xExtBack, points[-1][1] + yExtBack)

    extendedSplinePoints = points + [pointExtBack]

    return extendedSplinePoints

#Extends a list of points forward by taking the length and gradient of the last segment and inserting it at the end
def extendPointsFront(points):
    xExtFront = (points[1][0] - points[0][0])
    yExtFront = (points[1][1] - points[0][1])
    pointExtFront = (points[0][0] - xExtFront, points[0][1] - yExtFront)

    extendedSplinePoints = [pointExtFront] + points

    return extendedSplinePoints

#Extends a list of points at both ends by taking the length and gradient of the last segments and inserting it at the end
def extendPoints(points):
    return extendPointsFront(extendPointsBack(points))

#Offsets a list of points, or a singular point
def offsetPoints(points, offset, zoom, single = False, reverse = False):
    if not reverse:
        if not single:
            return [((point[0] * zoom) + offset[0], (point[1] * zoom) + offset[1]) for point in points]
        else:
            return (points[0] * zoom) + offset[0], (points[1] * zoom) + offset[1]
    else:
        if not single:
            return [((point[0] - offset[0]) / zoom, (point[1] - offset[1]) / zoom) for point in points]
        else:
            return (points[0] - offset[0]) / zoom, (points[1] - offset[1]) / zoom

#Calculates a point, a certain distance away from another point
def calculateSide(points, pointIndex, width):
    width = width / 2
    points = extendPointsBack(points)

    distance = pointDistance(points[pointIndex], points[pointIndex + 1])
    if distance == 0:
        return points[pointIndex][0], points[pointIndex][1]
    else:
        sideX = ((width * (points[pointIndex][1] - points[pointIndex + 1][1])) / distance) + points[pointIndex][0]
        sideY = ((width * (points[pointIndex + 1][0] - points[pointIndex][0])) / distance) + points[pointIndex][1]

    return sideX, sideY

def splitLineToNodes(startPos, endPos, nodeCount):
    lineLength = pointDistance(startPos, endPos)
    nodeSpacing = lineLength / (nodeCount - 1)
    nodes = []
    for node in range(int(nodeCount)):
        t = (nodeSpacing * node) / lineLength
        point = (((1 - t) * startPos[0]) + (t * endPos[0])), (((1 - t) * startPos[1]) + (t * endPos[1]))
        nodes.append(point)

    return nodes

#Used to combine two sides of a polygon (in the form of a list of points), to make one shape
def formPolygon(leftSide, rightSide, selectRange = None, close = False):
    if selectRange is None:
        newLeftSide = leftSide
        newRightSide = rightSide
    else:
        newLeftSide = leftSide[selectRange]
        newRightSide = rightSide[selectRange]

    if close:
        newLeftSide = newLeftSide + [leftSide[0]]
        newRightSide = newRightSide + [rightSide[0]]

    return newLeftSide + list(reversed(newRightSide))

#Checks whether a given point is on the screen
def checkIfOnscreen(pos, screenDimensions):
    return (0 <= pos[0] <= screenDimensions[0]) and (0 <= pos[1] <= screenDimensions[1])

#Convets meters to pixels using a scale
def mToPix(metres, pixelInMetres):
    return metres * (1 / pixelInMetres)

def sinDeg(degrees):
    return math.sin(degrees * math.pi / 180)
def cosDeg(degrees):
    return math.cos(degrees * math.pi / 180)
def tanDeg(degrees):
    return math.tan(degrees * math.pi / 180)

def pixToMiles(pixels, scale):
    meters = pixels * scale
    return int(meters * 2.237)
