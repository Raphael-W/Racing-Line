class UIElement:
    def __init__(self, layer, fontSize, colour, pos, stick):
        self.nonStickPosX = pos[0]
        self.nonStickPosY = pos[1]

        self.posX = pos[0]
        self.posY = pos[1]
        self.stick = stick.lower()

        self.font = layer.pygame.freetype.Font(layer.fontName, fontSize)
        self.colour = colour

        self.boundingBox = layer.pygame.Rect(0, 0, 0, 0)

        self.layer = layer
        layer.add(self)

    def update(self):
        pass

    def display(self):
        pass

    def returnBoundingBox(self):
        return self.boundingBox.topleft, self.boundingBox.topright, self.boundingBox.bottomleft, self.boundingBox.bottomright

    def stickyPos(self):
        vertValid = not(("n" in self.stick) and ("s" in self.stick))
        horValid = not (("e" in self.stick) and ("w" in self.stick))
        charValid = all([True for char in self.stick if char in ["n", "e", "s", "w"]])

        horStick = None
        vertStick = None
        for char in self.stick:
            if char in ["n", "s"]: vertStick = char
            elif char in ["e", "w"]: horStick = char

        newX = self.posX
        newY = self.posY
        if vertValid and horValid and charValid and (len(self.stick) > 0):
            if horStick == "e":
                newX = self.layer.screenWidth - self.nonStickPosX

            if vertStick == "s":
                newY = self.layer.screenHeight - self.nonStickPosY

        return newX, newY

class Button (UIElement):
    def __init__(self, layer, pos, stick, dimensions, text, fontSize, colour, action):
        super().__init__(layer, fontSize, colour, pos, stick)
        self.width = dimensions[0]
        self.height = dimensions[1]
        self.boundingBox = layer.pygame.Rect(self.posX, self.posY, self.width, self.height)

        self.text = text

        self.action = action

        self.mouseHovering = False
        self.mouseDownLast = False
        self.pointSelected = False

        self.baseColour = colour
        self.hoverColour = (colour[0] - 15, colour[1], colour[2])

    def update(self):
        mousePos = self.layer.pygame.mouse.get_pos()
        self.mouseHovering = (((self.posX + self.width / 2) + ((self.width / 2) + 2) > mousePos[0] > (self.posX + self.width / 2) - ((self.width / 2) + 2)) and
                              ((self.posY + self.height / 2) + ((self.height / 2) + 2) > mousePos[1] > (self.posY + self.height / 2) - ((self.height / 2) + 2)))

        if self.mouseHovering:
            self.colour = self.hoverColour
            self.pointSelected = self.mouseHovering and self.layer.pygame.mouse.get_pressed()[0] and not self.mouseDownLast
        else:
            self.colour = self.baseColour

        if self.pointSelected:
            self.action()
            self.pointSelected = False

        self.mouseDownLast = self.layer.pygame.mouse.get_pressed()[0]

    def display(self):
        self.boundingBox = self.layer.pygame.Rect(self.posX, self.posY, self.width, self.height)
        self.layer.pygame.draw.rect(self.layer.screen, self.colour, self.boundingBox, 0, 10)

        text_rect = self.font.get_rect(self.text)
        text_rect.center = self.boundingBox.center

        self.font.render_to(self.layer.screen, text_rect, self.text, (250, 250, 250))

class Label (UIElement):
    def __init__(self, layer, fontSize, pos, stick, text, colour):
        super().__init__(layer, fontSize, colour, pos, stick)
        self.text = text
        self.textSize = self.font.get_rect(self.text).size
        self.boundingBox = layer.pygame.Rect(self.posX, self.posY, self.textSize[0], self.textSize[1])

    def display(self):
        self.font.render_to(self.layer.screen, (self.posX, self.posY), self.text, self.colour)

class Slider (UIElement): #Use label class for label
    def __init__(self, layer, fontSize, barColour, handleColour, pos, stick, size, length, valueRange, value = 0, action = None):
        super().__init__(layer, fontSize, barColour, pos, stick)

        self.barColour = barColour

        self.handleColour = handleColour
        self.selectedHandleColour = (handleColour[0] - (handleColour[0] * 0.4),
                                     handleColour[1] - (handleColour[1] * 0.4),
                                     handleColour[2] - (handleColour[2] * 0.4))
        self.displayColour = handleColour

        self.size = size
        self.length = length
        self.valueRange = valueRange

        self.mouseHovering = False
        self.handleX = ((self.length / (self.valueRange[1] - self.valueRange[0])) * value) - valueRange[0]
        self.handleSelected = False
        self.mouseDownLast = False
        self.handleSize = 0

        self.value = value
        self.action = action

    def update(self):
        mouseX, mouseY = self.layer.pygame.mouse.get_pos()
        self.handleSize = 12 * self.size
        self.boundingBox = self.layer.pygame.Rect(self.posX + self.handleX - self.handleSize, self.posY - (self.handleSize * 0.75), self.handleSize * 2, self.handleSize * 2)
        self.mouseHovering = (((self.posX + self.handleX) + (self.handleSize + 2) > mouseX > (self.posX + self.handleX) - (self.handleSize + 2)) and
                              (self.posY + (self.handleSize + 2) > mouseY > self.posY - (self.handleSize + 2)))

        if self.mouseHovering or self.handleSelected:
            self.displayColour = self.selectedHandleColour
        else:
            self.displayColour = self.handleColour

        if not self.layer.pygame.mouse.get_pressed()[0]:
            self.handleSelected = False

        if self.handleSelected:
            if self.action is not None:
                self.action()

            if self.posX < mouseX < (self.posX + self.length):
                self.handleX = mouseX - self.posX
                self.value = (self.handleX / (self.length / (self.valueRange[1] - self.valueRange[0]))) + self.valueRange[0]

        if not self.handleSelected:
            self.handleSelected = self.mouseHovering and self.layer.pygame.mouse.get_pressed()[0] and not self.mouseDownLast

        self.mouseDownLast = self.layer.pygame.mouse.get_pressed()[0]

    def display(self):
        bar = self.layer.pygame.Rect(self.posX, self.posY, self.length, 7 * self.size)
        self.layer.pygame.draw.rect(self.layer.screen, self.barColour, bar, 0, 100)
        self.font.render_to(self.layer.screen, (self.posX + self.length + 10, self.posY - 3), str(int(self.value)), self.barColour)
        self.layer.pygame.draw.circle(self.layer.screen, self.displayColour, (self.posX + self.handleX, self.posY + (7 * self.size) / 2), self.handleSize)

class Switch (UIElement): #Use label class for label
    def __init__(self, layer, colour, pos, stick, size, value = True, action = None):
        super().__init__(layer, 0, colour, pos, stick)

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
        mouseX, mouseY = self.layer.pygame.mouse.get_pos()

        self.mouseHovering = ((self.posX + self.barWidth > mouseX > self.posX) and (self.posY + self.barHeight > mouseY > self.posY))

        if self.mouseHovering:
            #self.colour = self.hoverColour
            self.pointSelected = self.mouseHovering and self.layer.pygame.mouse.get_pressed()[0] and not self.mouseDownLast
        else:
            #self.colour = self.baseColour
            pass

        if self.pointSelected:
            self.value = not self.value
            self.pointSelected = False

            if self.action is not None:
                self.action()

        if self.value:
            self.colour = (41, 66, 43)
        else:
            self.colour = (66, 41, 41)

        self.mouseDownLast = self.layer.pygame.mouse.get_pressed()[0]

    def display(self):
        self.boundingBox = self.layer.pygame.Rect(self.posX, self.posY, self.barWidth, self.barHeight)
        self.layer.pygame.draw.rect(self.layer.screen, self.colour, self.boundingBox, 0, 100)

        if self.value:
            circleOffset = (self.barWidth / 2)
        else:
            circleOffset = 0

        self.layer.pygame.draw.circle(self.layer.screen, (20, 20, 20), (self.posX + (self.barWidth / 4) + circleOffset, self.posY + (self.barHeight / 2)), 10 * self.size)


class Layer:
    def __init__(self, name, number, screen, pygame, fontName):
        self.name = name
        self.number = number
        self.elements = []

        self.screen = screen
        self.pygame = pygame
        self.fontName = fontName

        self.screenWidth = 0
        self.screenHeight = 0

    def add(self, element):
        self.elements.append(element)

    def display(self, screenWidth, screenHeight):
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight
        for element in self.elements:
            element.posX, element.posY = element.stickyPos()
            element.update()
            element.display()

    def mouseOnLayer(self, mousePos):
        boundingBoxes = [element.returnBoundingBox() for element in self.elements]
        hovering = False
        mouseX, mouseY = mousePos

        for i in boundingBoxes:
            hovering = hovering or ((i[0][0] < mouseX < i[1][0]) and (i[0][1] < mouseY < i[2][1]))

        return hovering
