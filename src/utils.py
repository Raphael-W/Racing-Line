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
    distance12 = pointDistance(point1, point2)
    distance23 = pointDistance(point2, point3)
    distance31 = pointDistance(point3, point1)

    cosAngle = ((distance12 ** 2) + (distance23 ** 2) - (distance31 ** 2)) / (2 * distance12 * distance23)
    cosAngle = max(min(cosAngle, 1), -1)
    angleRad = math.acos(cosAngle)
    angleDegrees = angleRad * (180.0 / math.pi)

    return angleDegrees

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

#Used to combine two sides of a polygon (in the form of a list of points), to make one shape
def formPolygon(leftSide, rightSide, selectRange, close = False):
    newLeftSide = leftSide[selectRange]
    newRightSide = rightSide[selectRange]
    if close:
        newLeftSide += [leftSide[0]]
        newRightSide += [rightSide[0]]

    return newLeftSide + list(reversed(newRightSide))

#Checks whether a given point is on the screen
def checkIfOnscreen(pos, screenDimensions):
    return (0 <= pos[0] <= screenDimensions[0]) and (0 <= pos[1] <= screenDimensions[1])
