import itertools
from threading import Thread

from utils import *

class RacingLine:
    def __init__(self, pygame, screen, track):
        self.pygame = pygame
        self.screen = screen

        self.maxSpeed = 515
        self.maxAcceleration = 500
        self.maxAngle = 8
        self.weight = 800  #kg

        self.track = track
        self.clonedTrack = self.track.cloneTrack()
        self.xResolution = 1
        self.zResolution = 20
        self.zSteps = self.maxSpeed / self.zResolution

        self.nodes = []
        self.racingLine = []

    def clearLine(self):
        self.nodes = []

    def calculateCosts(self, node1, node2 = None, previousBearing = None, node2Coords = None):
        node1Pos = self.nodes[node1[0]][node1[1]][node1[2]]
        node1Vel = self.zSteps * node1[1]

        if node2Coords is None:
            node2Pos = self.nodes[node2[0]][node2[1]][node2[2]]
            node2Vel = self.zSteps * node2[1]
        else:
            node2Pos = node2Coords
            node2Vel = 30

        distance = pointDistance(node1Pos, node2Pos)
        timeCost = distance / ((node1Vel + node2Vel) / 2)

        constraintCost = 0
        if tuple(node1Pos) == tuple(node2Pos):
            constraintCost = 10000000000

        if constraintCost == 0:
            acceleration = (abs(node2Vel - node1Vel) / timeCost)
            if acceleration > self.maxAcceleration:
                constraintCost = 10000000000

        if (constraintCost == 0) and (previousBearing is not None):
            changeInDir = abs(previousBearing - bearing(node1Pos, node2Pos))
            if changeInDir > (self.maxAngle - (node1Vel / 170)):
                constraintCost = 10000000000

        return timeCost + constraintCost

    def defineNodes(self):
        self.nodes = []
        leftEdge, rightEdge = self.clonedTrack.getEdgePoints()
        nodeCount = self.clonedTrack.width / self.xResolution
        startCoords, startAngle, startIndex, startDir = self.track.getStartPos()

        if not startDir:
            direction = 1
            endIndex = startIndex + len(leftEdge)
        else:
            direction = -1
            endIndex = startIndex - len(leftEdge)

        for pointIndex in range(startIndex, endIndex, direction):
            pointIndex = pointIndex % len(leftEdge)
            rowNodes = splitLineToNodes(leftEdge[pointIndex], rightEdge[pointIndex], nodeCount)
            allVelocities = [rowNodes for _ in range(self.zResolution)]
            self.nodes.append(allVelocities)

    def findShortestPath(self):
        pathStart = self.track.getStartPos()[0]
        paths = [[[(len(self.nodes) - 1, velocityIndex, nodeIndex)], self.calculateCosts((len(self.nodes) - 1, velocityIndex, nodeIndex), node2Coords = pathStart), bearing(self.nodes[-1][velocityIndex][nodeIndex], pathStart)] for velocityIndex, nodeIndex in itertools.product(range(1, self.zResolution), range(len(self.nodes[0][0])))]
        for splineIndex in range(len(self.nodes) - 1):
            newPaths = []
            for velocityIndex, nodeIndex in itertools.product(range(1, self.zResolution), range(len(self.nodes[0][0]))):
                costs = []
                for node in paths:
                    costToNextNode = self.calculateCosts((splineIndex, velocityIndex, nodeIndex), node[0][-1], node[2])
                    costs.append(costToNextNode + node[1])
                quickest = np.argmin(costs)
                previousNodeIndexes = paths[quickest][0][-1]

                listOfPoints = (paths[quickest][0] + [[splineIndex, velocityIndex, nodeIndex]])
                newCost = costs[quickest]
                newBearing = bearing(self.nodes[splineIndex][velocityIndex][nodeIndex], self.nodes[previousNodeIndexes[0]][previousNodeIndexes[1]][previousNodeIndexes[2]])
                newPaths.append([listOfPoints, newCost, newBearing])

            paths = newPaths

        times = [path[1] for path in paths]
        quickest = np.argmin(times)
        print(times[quickest])
        self.racingLine = [[self.nodes[index[0]][index[1]][index[2]], index[1]] for index in paths[quickest][0]]

    def computeRacingLine(self):
        def sequence():
            self.clonedTrack = self.track.cloneTrack(resolution = 10)
            self.clonedTrack.deKink()
            self.defineNodes()
            self.findShortestPath()

        thread = Thread(target = sequence, daemon = True)
        thread.start()

    def display(self, offset, zoom):
        for point in self.racingLine:
            speedColour = (255 / self.zResolution) * point[1]
            offsetPoint = offsetPoints(point[0], offset, zoom, True)
            self.pygame.draw.circle(self.screen, (speedColour, 0, 0), offsetPoint, 3)

    def displayNodes(self, offset, zoom):
        for splineIndex in self.nodes:
            for point in splineIndex[0]:
                offsetPoint = offsetPoints(point, offset, zoom, True)
                self.pygame.draw.circle(self.screen, (200, 200, 200), offsetPoint, 3)
