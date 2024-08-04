from utils import *

class Ray:
    def __init__(self, points, reverseSearch = False, colour = (255, 0, 0)):
        self.posX, self.posY = (0, 0)
        self.angle = 0
        self.points = points
        self.startingIndex = 0
        self.reverseSearch = reverseSearch
        if reverseSearch:
            self.points = list((reversed(self.points)))

        self.colour = colour

        self.lastPointsIndex = sum([len(l) for l in self.points]) - 1

        self.collisionCoords = (0, 0)
        self.distance = float('inf')

    def findCollision(self, startPos, angle, startIndex):
        self.posX, self.posY = startPos
        self.angle = angle

        if self.reverseSearch:
            self.startingIndex = min(startIndex + 10, self.lastPointsIndex)
            points = [(l[(len(l) - 1) - self.startingIndex:] + l[:(len(l) - 1) - self.startingIndex]) for l in self.points]
        else:
            self.startingIndex = max(startIndex - 10, 0)
            points = [(l[self.startingIndex:] + l[:self.startingIndex]) for l in self.points]

        intersectionFound = False
        currentIndex = 0

        rayM = tanDeg(self.angle) * -1
        rayC = self.posY - (rayM * self.posX)
        while not intersectionFound and (currentIndex < (self.lastPointsIndex - 1)):
            self.distance = float('inf')
            self.collisionCoords = (0, 0)

            listToSearch = currentIndex % len(points)
            indexOfList = currentIndex // len(points)
            currentLine = (points[listToSearch][indexOfList], points[listToSearch][indexOfList + 1])
            intersection = lineSegmentIntersection(currentLine[0], currentLine[1], rayM, rayC, angle, startPos)
            if intersection is not None:
                self.collisionCoords = intersection
                self.distance = pointDistance((self.posX, self.posY), intersection)
                return intersection

            currentIndex += 1

    def updatePoints(self, newPoints, reverseSearch = False):
        self.points = newPoints
        self.lastPointsIndex = sum([len(l) for l in self.points]) - 1
        self.reverseSearch = reverseSearch
        if reverseSearch:
            self.points = [list(reversed(l)) for l in self.points]

    def display(self, pygame, screen, offset, zoom):
        if self.distance < float('inf'):
            startPos = offsetPoints((self.posX, self.posY), offset, zoom, single = True)
            endPos = offsetPoints(self.collisionCoords, offset, zoom, single = True)
            pygame.draw.line(screen, self.colour, startPos, endPos)
