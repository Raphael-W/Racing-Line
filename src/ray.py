class Ray:
    def __init__(self, position, angle, points, startingIndex = 0, colour = (255, 0, 0)):
        self.posX, self.posY = position
        self.angle = angle
        self.points = points
        self.startingIndex = startingIndex
        self.colour = colour

        self.distance = float('inf')

    def update(self):
        pass

    def display(self, pygame, screen):
        if self.distance < float('inf'):
            pass
