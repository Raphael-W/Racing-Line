#Make UI Element class, and make others inherit from it
class Button:
    def __init__(self, screen, pygame, font, pos, dimensions, text, fontSize, colour, action):
        self.screen = screen
        self.pygame = pygame
        self.font = font
        self.fontSize = fontSize
        self.font.size = fontSize

        self.posX = pos[0]
        self.posY = pos[1]

        self.width = dimensions[0]
        self.height = dimensions[1]
        self.rectangleBox = self.pygame.Rect(self.posX, self.posY, self.width, self.height)

        self.text = text
        self.colour = colour

        self.action = action

        self.mouseHovering = False
        self.mouseDownLast = False
        self.pointSelected = False

        self.baseColour = colour
        self.hoverColour = (colour[0] - 15, colour[1], colour[2])

    def update(self):
        mousePos = self.pygame.mouse.get_pos()
        self.mouseHovering = (((self.posX + self.width / 2) + ((self.width / 2) + 2) > mousePos[0] > (self.posX + self.width / 2) - ((self.width / 2) + 2)) and
                              ((self.posY + self.height / 2) + ((self.height / 2) + 2) > mousePos[1] > (self.posY + self.height / 2) - ((self.height / 2) + 2)))

        if self.mouseHovering:
            self.colour = self.hoverColour
            self.pointSelected = self.mouseHovering and self.pygame.mouse.get_pressed()[0] and not self.mouseDownLast
        else:
            self.colour = self.baseColour

        if self.pointSelected:
            self.action()
            self.pointSelected = False

        self.mouseDownLast = self.pygame.mouse.get_pressed()[0]

    def display(self):
        self.update()
        self.pygame.draw.rect(self.screen, self.colour, self.rectangleBox, 0, 10)

        text_rect = self.font.get_rect(self.text)
        text_rect.center = self.rectangleBox.center

        self.font.render_to(self.screen, text_rect, self.text, (250, 250, 250))

    def returnBoundingBox(self):
        return self.rectangleBox.topleft, self.rectangleBox.topright, self.rectangleBox.bottomleft, self.rectangleBox.bottomright

class Label:
    def __init__(self, screen, pygame, pos, size, text):
        self.screen = screen
        self.pos = pos
        self.size = size
        self.text = text

class Slider: #Use label class for label
    def __init__(self, screen, pygame, pos, size, length, valueRange, text, localLabelPos, value = 0, action = None):
        self.screen = screen
        self.pos = pos
        self.size = size
        self.length = length
        self.valueRange = valueRange
        self.text = text
        self.localLabelPos = localLabelPos

        self.value = value
        self.action = action

class CheckBox: #Use label class for label
    def __init__(self, screen, pygame, pos, size, text, localLabelPos, value = False, action = None):
        self.screen = screen
        self.pos = pos
        self.size = size
        self.text = text
        self.localLabelPos = localLabelPos

        self.value = value
        self.action = action

class Layer:
    def __init__(self, name, number):
        self.name = name
        self.number = number
        self.elements = []

    def add(self, UIElement):
        self.elements.append(UIElement)

    def mouseOnLayer(self, mousePos):
        boundingBoxes = [element.returnBoundingBox() for element in self.elements]
        hovering = False
        mouseX, mouseY = mousePos

        for i in boundingBoxes:
            hovering = hovering or ((i[0][0] < mouseX < i[1][0]) and (i[0][1] < mouseY < i[2][1]))

        return hovering
