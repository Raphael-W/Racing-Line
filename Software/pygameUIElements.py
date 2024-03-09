class UIElement:
    def __init__(self, layer, screen, pygame, font, fontSize, text, colour, pos):
        self.screen = screen
        self.pygame = pygame

        self.posX = pos[0]
        self.posY = pos[1]

        self.text = str(text)
        self.font = pygame.freetype.Font(font, fontSize)
        self.colour = colour

        self.boundingBox = pygame.Rect(0, 0, 0, 0)
        layer.add(self)

    def update(self):
        pass

    def display(self):
        pass

    def returnBoundingBox(self):
        return self.boundingBox.topleft, self.boundingBox.topright, self.boundingBox.bottomleft, self.boundingBox.bottomright

class Button (UIElement):
    def __init__(self, layer, screen, pygame, font, pos, dimensions, text, fontSize, colour, action):
        super().__init__(layer, screen, pygame, font, fontSize, text, colour, pos)

        self.width = dimensions[0]
        self.height = dimensions[1]
        self.boundingBox = self.pygame.Rect(self.posX, self.posY, self.width, self.height)

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
        self.pygame.draw.rect(self.screen, self.colour, self.boundingBox, 0, 10)

        text_rect = self.font.get_rect(self.text)
        text_rect.center = self.boundingBox.center

        self.font.render_to(self.screen, text_rect, self.text, (250, 250, 250))

class Label (UIElement):
    def __init__(self, layer, screen, pygame, font, fontSize, pos, text, colour):
        super().__init__(layer, screen, pygame, font, fontSize, text, colour, pos)
        self.textSize = self.font.get_rect(self.text).size
        self.boundingBox = pygame.Rect(self.posX, self.posY, self.textSize[0], self.textSize[1])

    def display(self):
        self.font.render_to(self.screen, (self.posX, self.posY), self.text, self.colour)

class Slider (UIElement): #Use label class for label
    def __init__(self, layer, screen, pygame, font, fontSize, text, barColour, handleColour, pos, size, length, valueRange, value = 0, action = None):
        super().__init__(layer, screen, pygame, font, fontSize, text, barColour, pos)

        self.barColour = barColour
        self.handleColour = handleColour
        self.size = size
        self.length = length
        self.valueRange = valueRange

        self.mouseHovering = False
        self.handleX = (self.length / (self.valueRange[1] - self.valueRange[0])) * value
        self.handleSelected = False
        self.mouseDownLast = False
        self.handleSize = 0

        self.value = value
        self.action = action

    def update(self):
        mouseX, mouseY = self.pygame.mouse.get_pos()
        self.handleSize = 12 * self.size
        self.boundingBox = self.pygame.Rect(self.posX + self.handleX - self.handleSize, self.posY - (self.handleSize * 0.75), self.handleSize * 2, self.handleSize * 2)
        self.mouseHovering = (((self.posX + self.handleX) + (self.handleSize + 2) > mouseX > (self.posX + self.handleX) - (self.handleSize + 2)) and
                              (self.posY + (self.handleSize + 2) > mouseY > self.posY - (self.handleSize + 2)))

        if self.mouseHovering or self.handleSelected:
            self.handleColour = (0, 200, 0)
        else:
            self.handleColour = (200, 0, 0)

        if not self.pygame.mouse.get_pressed()[0]:
            self.handleSelected = False

        if self.handleSelected:
            if self.posX < mouseX < (self.posX + self.length):
                self.handleX = mouseX - self.posX
                self.value = self.handleX / (self.length / (self.valueRange[1] - self.valueRange[0]))

        if not self.handleSelected:
            self.handleSelected = self.mouseHovering and self.pygame.mouse.get_pressed()[0] and not self.mouseDownLast

        self.mouseDownLast = self.pygame.mouse.get_pressed()[0]

    def display(self):
        bar = self.pygame.Rect(self.posX, self.posY, self.length, 7 * self.size)
        self.pygame.draw.rect(self.screen, self.barColour, bar, 0, 100)

        self.pygame.draw.circle(self.screen, self.handleColour, (self.posX + self.handleX, self.posY + (7 * self.size) / 2), self.handleSize)

class Switch (UIElement): #Use label class for label
    def __init__(self, layer, screen, pygame, font, colour, pos, size, value = True, action = None):
        super().__init__(layer, screen, pygame, font, 0, "", colour, pos)

        self.size = size
        self.value = value
        self.action = action

        self.barWidth = 0
        self.barHeight = 0

        self.mouseHovering = False
        self.pointSelected = False
        self.mouseDownLast = False

    def update(self):
        self.barWidth = 55 * self.size
        self.barHeight = 25 * self.size
        mouseX, mouseY = self.pygame.mouse.get_pos()

        self.mouseHovering = ((self.posX + self.barWidth > mouseX > self.posX) and (self.posY + self.barHeight > mouseY > self.posY))

        if self.mouseHovering:
            #self.colour = self.hoverColour
            self.pointSelected = self.mouseHovering and self.pygame.mouse.get_pressed()[0] and not self.mouseDownLast
        else:
            #self.colour = self.baseColour
            pass

        if self.pointSelected:
            self.value = not(self.value)
            self.pointSelected = False

        if self.value:
            self.colour = (41, 66, 43)
        else:
            self.colour = (66, 41, 41)

        self.mouseDownLast = self.pygame.mouse.get_pressed()[0]

    def display(self):
        self.boundingBox = self.pygame.Rect(self.posX, self.posY, self.barWidth, self.barHeight)
        self.pygame.draw.rect(self.screen, self.colour, self.boundingBox, 0, 100)

        if self.value:
            circleOffset = (self.barWidth / 2)
        else:
            circleOffset = 0

        self.pygame.draw.circle(self.screen, (20, 20, 20), (self.posX + (self.barWidth / 4) + circleOffset, self.posY + (self.barHeight / 2)), 10 * self.size)


class Layer:
    def __init__(self, name, number):
        self.name = name
        self.number = number
        self.elements = []

    def add(self, UIElement):
        self.elements.append(UIElement)

    def display(self):
        for element in self.elements:
            element.update()
            element.display()

    def mouseOnLayer(self, mousePos):
        boundingBoxes = [element.returnBoundingBox() for element in self.elements]
        hovering = False
        mouseX, mouseY = mousePos

        for i in boundingBoxes:
            hovering = hovering or ((i[0][0] < mouseX < i[1][0]) and (i[0][1] < mouseY < i[2][1]))

        return hovering
