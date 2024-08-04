import pygame.draw
from scipy.spatial import KDTree
from pygame import Vector2

from utils import *
from ray import *

class Car:
    def __init__(self, pygame, screen, directories, track):
        self.pygame = pygame
        self.screen = screen

        self.position = Vector2(50, 50)
        self.scale = 0.2

        self.velocity = Vector2(0.0, 0.0)
        self.acceleration = 0
        self.steering = 0
        self.rotation = 0
        self.previousRotation = self.rotation

        self.steeringInput = 0
        self.accelerationInput = 0

        self.maxSpeed = 515
        self.maxAcceleration = 120
        self.maxTurningAngle = 40
        self.brakeDeceleration = 200
        self.freeDeceleration = 10

        self.width = mToPix(2, self.scale)
        self.wheelBase = mToPix(0.7, self.scale) #1.93

        self.carBody = None
        self.transformedCarBody = None
        self.carBodyRect = None

        self.carWheelR = None
        self.transformedCarWheelR = None
        self.carWheelRRect = None

        self.carWheelL = None
        self.transformedCarWheelL = None
        self.carWheelLRect = None

        self.carSurface = None

        self.modelMultiplier = 1

        self.zoom = 1
        self.previousZoom = 0
        self.offset = (0, 0)

        self.show = True
        self.dead = False
        self.offTrack = False
        self.previouslyOffTrack = False

        self.directories = directories
        self.track = track
        self.nearestSplineIndex = None

        self.forwardRay = Ray(self.track.getEdgePoints(), self.track.finishDir)
        self.leftRay = Ray(self.track.getEdgePoints(), self.track.finishDir)
        self.rightRay = Ray(self.track.getEdgePoints(), self.track.finishDir)
        self.leftDiagonalRay = Ray(self.track.getEdgePoints(), self.track.finishDir)
        self.rightDiagonalRay = Ray(self.track.getEdgePoints(), self.track.finishDir)
        self.leftDiagonalSteepRay = Ray(self.track.getEdgePoints(), self.track.finishDir)
        self.rightDiagonalSteepRay = Ray(self.track.getEdgePoints(), self.track.finishDir)

        self.rays = [self.forwardRay, self.leftRay, self.rightRay, self.leftDiagonalRay, self.rightDiagonalRay, self.leftDiagonalSteepRay, self.rightDiagonalSteepRay]

    def setPosition(self, posX, posY, facing = 0):
        self.position = Vector2(posX, posY)
        self.rotation = facing
        self.velocity = Vector2(0, 0)
        self.acceleration = 0

    def reset(self):
        startPos, startAngle = self.track.getStartPos()
        self.nearestSplineIndex = None
        self.setPosition(*startPos, startAngle)
        self.dead = False

    def trackChanged(self):
        for ray in self.rays:
            ray.updatePoints(self.track.getEdgePoints(), not self.track.finishDir)

    def updateNearestSplineIndex(self):
        if len(self.track.points) >= 2:
            previousIndex = self.nearestSplineIndex
            listLength = len(self.track.splinePoints)

            if self.nearestSplineIndex is None:
                pointsIndex = list(range(listLength))
                points = self.track.splinePoints
            else:
                pointsIndex = [i % listLength for i in range(previousIndex - 10, previousIndex + 10)]
                points = [self.track.splinePoints[i] for i in pointsIndex]

            tree = KDTree(points)
            index = tree.query(self.position)[1]
            index += (pointsIndex[index] - index)
            self.nearestSplineIndex = index

    def updateIsDead(self):
        if not self.dead and (len(self.track.points) >= 2):
            points = extendPoints(self.track.splinePoints)
            width = self.track.width * (1 / self.track.scale)
            index = self.nearestSplineIndex + 1

            distanceFromCenter = lineToPointDistance(points[(index - 1) % len(points)], points[(index + 1) % (len(points))], self.position)
            self.dead = self.dead and distanceFromCenter[0] > (width / 2)
            self.previouslyOffTrack = self.offTrack
            self.offTrack = distanceFromCenter[0] > (width / 2)

    def display(self):
        if self.show:
            self.transformedCarWheelR = self.pygame.transform.rotate(self.carWheelR, (self.steeringInput * self.maxTurningAngle))
            self.transformedCarWheelL = self.pygame.transform.rotate(self.carWheelL, (self.steeringInput * self.maxTurningAngle))

            self.carWheelRRect = self.transformedCarWheelR.get_rect()
            self.carWheelLRect = self.transformedCarWheelL.get_rect()

            self.carWheelRRect.center = (436, 281)
            self.carWheelLRect.center = (64, 281)

            if self.offTrack != self.previouslyOffTrack:
                if self.offTrack:
                    self.carBody.fill((220, 0, 0), special_flags = 4) #BLEND_RGB_MIN
                    self.carWheelR.fill((220, 0, 0), special_flags = 4) #BLEND_RGB_MIN
                    self.carWheelL.fill((220, 0, 0), special_flags = 4) #BLEND_RGB_MIN
                else:
                    self.carBody.fill((255, 255, 255), special_flags = 5)  #BLEND_RGB_MAX
                    self.carWheelR.fill((255, 255, 255), special_flags = 5)  #BLEND_RGB_MAX
                    self.carWheelL.fill((255, 255, 255), special_flags = 5)  #BLEND_RGB_MAX

            self.carSurface = self.pygame.Surface((500, 963), self.pygame.SRCALPHA).convert_alpha()
            self.carSurface.blit(self.transformedCarBody, self.carBodyRect)
            self.carSurface.blit(self.transformedCarWheelR, self.carWheelRRect)
            self.carSurface.blit(self.transformedCarWheelL, self.carWheelLRect)

            self.carSurface = self.pygame.transform.scale_by(self.carSurface, self.modelMultiplier)
            self.carSurface = self.pygame.transform.rotate(self.carSurface, self.rotation - 90)
            surfaceRect = self.carSurface.get_rect(center = offsetPoints(self.position, self.offset, self.zoom, True))

            self.screen.blit(self.carSurface, (surfaceRect.x, surfaceRect.y))

            if not self.offTrack:
                for ray in self.rays:
                    ray.display(self.pygame, self.screen, self.offset, self.zoom)

    def update(self, steeringInput, accelerationInput, offset, zoom, deltaTime):
        self.zoom = zoom
        self.offset = offset
        self.modelMultiplier = self.zoom * (1 / 500) * self.width #0.02 at zoom = 1

        if self.carBody is None:
            self.carBody = self.transformedCarBody = self.pygame.image.load(self.directories["f1Car"]).convert_alpha()
            self.carWheelR = self.transformedCarWheelR = self.pygame.image.load(self.directories["f1Wheel"]).convert_alpha()
            self.carWheelL = self.transformedCarWheelL = self.pygame.image.load(self.directories["f1Wheel"]).convert_alpha()

            self.carBodyRect = self.transformedCarBody.get_rect()
            self.carBodyRect.topleft = (0, 0)

        # ---- Movement ----
        self.updateNearestSplineIndex()
        self.updateIsDead()

        self.steeringInput = -steeringInput
        self.accelerationInput = accelerationInput

        if self.accelerationInput > 0:
            if self.acceleration < 0:
                self.acceleration = 0

            if self.velocity.x == 0:
                self.acceleration = self.maxAcceleration
            else:
                self.acceleration = ((self.maxAcceleration * 100) / self.velocity.x) * self.accelerationInput

        elif self.accelerationInput < 0:
            self.acceleration = -self.brakeDeceleration * abs(self.accelerationInput)

        else:
            if abs(self.velocity.x) > deltaTime * self.freeDeceleration:
                self.acceleration = -math.copysign(self.freeDeceleration, self.velocity.x)
            else:
                if deltaTime != 0:
                    self.acceleration = -self.velocity.x / deltaTime

        self.acceleration = max(-self.brakeDeceleration, min(self.acceleration, self.maxAcceleration))

        self.steering = self.steeringInput * self.maxTurningAngle * deltaTime * 10

        limitedSpeed = self.maxSpeed * self.accelerationInput
        if self.accelerationInput <= 0:
            limitedSpeed = self.maxSpeed

        self.velocity += (self.acceleration * deltaTime, 0)
        self.velocity.x = max(min(self.velocity.x, limitedSpeed), 0)

        if self.steering:
            turningRadius = (self.wheelBase / math.sin(math.radians(self.steering))) + math.copysign((self.velocity.x / 10) ** 1.5, self.steering)
            angularVelocity = self.velocity.x / turningRadius
        else:
            angularVelocity = 0

        self.position += self.velocity.rotate(-self.rotation) * deltaTime
        self.rotation += math.degrees(angularVelocity) * deltaTime

        if not self.offTrack:
            self.forwardRay.findCollision(self.position, self.rotation, self.nearestSplineIndex)
            self.leftRay.findCollision(self.position, self.rotation - 90, self.nearestSplineIndex)
            self.rightRay.findCollision(self.position, self.rotation + 90, self.nearestSplineIndex)
            self.leftDiagonalRay.findCollision(self.position, self.rotation - 45, self.nearestSplineIndex)
            self.rightDiagonalRay.findCollision(self.position, self.rotation + 45, self.nearestSplineIndex)
            self.leftDiagonalSteepRay.findCollision(self.position, self.rotation - 20, self.nearestSplineIndex)
            self.rightDiagonalSteepRay.findCollision(self.position, self.rotation + 20, self.nearestSplineIndex)

        self.previousZoom = self.zoom
