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

        self.maxSpeed = 500
        self.maxAcceleration = 300
        self.maxTurningAngle = 40
        self.brakeDeceleration = 200
        self.freeDeceleration = 50

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

        self.directories = directories
        self.track = track
        self.nearestSplineIndex = 0

    def setPosition(self, posX, posY, facing = 0):
        self.position = Vector2(posX, posY)
        self.rotation = facing
        self.velocity = Vector2(0, 0)
        self.acceleration = 0

    def updateNearestSplineIndex(self):
        points = self.track.splinePoints
        tree = KDTree(points)
        dist, index = tree.query(self.position)
        self.nearestSplineIndex = index

    def updateIsDead(self):
        if True:#not self.dead:
            points = extendPoints(self.track.splinePoints)
            width = self.track.width * (1 / self.track.scale)
            index = self.nearestSplineIndex + 1

            distanceFromCenter = lineToPointDistance(points[index - 1], points[(index + 1) % (len(points) + 1)], self.position)
            self.dead = distanceFromCenter[0] > (width / 2)
            return distanceFromCenter[1], points[index - 1], points[(index + 1) % len(points)]

    def display(self):
        if self.show:
            self.transformedCarWheelR = self.pygame.transform.rotate(self.carWheelR, (self.steeringInput * self.maxTurningAngle))
            self.transformedCarWheelL = self.pygame.transform.rotate(self.carWheelL, (self.steeringInput * self.maxTurningAngle))

            self.carWheelRRect = self.transformedCarWheelR.get_rect()
            self.carWheelLRect = self.transformedCarWheelL.get_rect()

            self.carWheelRRect.center = (436, 281)
            self.carWheelLRect.center = (64, 281)

            self.carSurface = self.pygame.Surface((500, 963), self.pygame.SRCALPHA).convert_alpha()
            self.carSurface.blit(self.transformedCarBody, self.carBodyRect)
            self.carSurface.blit(self.transformedCarWheelR, self.carWheelRRect)
            self.carSurface.blit(self.transformedCarWheelL, self.carWheelLRect)

            self.carSurface = self.pygame.transform.scale_by(self.carSurface, self.modelMultiplier)
            self.carSurface = self.pygame.transform.rotate(self.carSurface, self.rotation - 90)
            surfaceRect = self.carSurface.get_rect(center = offsetPoints(self.position, self.offset, self.zoom, True))

            self.screen.blit(self.carSurface, (surfaceRect.x, surfaceRect.y))

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

        self.velocity += (self.acceleration * deltaTime, 0)
        self.velocity.x = max(min(self.velocity.x, self.maxSpeed), 0)

        if self.steering:
            turningRadius = (self.wheelBase / math.sin(math.radians(self.steering))) + math.copysign(self.velocity.x / 4, self.steering)
            angularVelocity = self.velocity.x / turningRadius
        else:
            angularVelocity = 0

        self.position += self.velocity.rotate(-self.rotation) * deltaTime
        self.rotation += math.degrees(angularVelocity) * deltaTime

        self.previousZoom = self.zoom
