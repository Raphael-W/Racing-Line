class UIElement:
    def __init__(self, layer, pos, stick, show = True, layerIndex = -1):
        self.nonStickPosX = pos[0]
        self.nonStickPosY = pos[1]

        self.posX = pos[0]
        self.posY = pos[1]
        self.stick = stick.lower()

        self.boundingBox = layer.pygame.Rect(0, 0, 0, 0)

        self.layer = layer
        self.layerIndex = layerIndex

        self.show = show

        layer.add(self)

    def update(self):
        pass

    def offsetPos(self, offset):
        if offset is not None:
            offsetX, offsetY = self.layer.offset

            offsetPosX = self.posX + offsetX
            offsetPosY = self.posY + offsetY

            return  offsetPosX, offsetPosY

        return self.posX, self.posY

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
    def __init__(self, layer, pos, stick, dimensions, text, fontSize, colour, textOffset = (0, 0), roundedCorners = 10, action = None, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)
        self.width = dimensions[0]
        self.height = dimensions[1]
        self.boundingBox = layer.pygame.Rect(self.posX, self.posY, self.width, self.height)
        self.roundedCorers = roundedCorners

        self.text = text
        self.textOffset = textOffset
        self.font = layer.pygame.freetype.Font(layer.fontName, fontSize)

        self.action = action

        self.mouseHovering = False
        self.actionRun = False
        self.pointSelected = False

        self.colour = colour
        self.baseColour = colour
        self.hoverColour = (colour[0] - (colour[0] * 0.2),
                            colour[1] - (colour[1] * 0.2),
                            colour[2] - (colour[2] * 0.2))

        self.pressedColour = (colour[0] - (colour[0] * 0.4),
                              colour[1] - (colour[1] * 0.4),
                              colour[2] - (colour[2] * 0.4))

    def update(self):
        mousePos = self.layer.pygame.mouse.get_pos()
        self.mouseHovering = (((self.posX + self.width / 2) + ((self.width / 2) + 2) > mousePos[0] > (self.posX + self.width / 2) - ((self.width / 2) + 2)) and
                              ((self.posY + self.height / 2) + ((self.height / 2) + 2) > mousePos[1] > (self.posY + self.height / 2) - ((self.height / 2) + 2)))

        if self.mouseHovering:
            self.colour = self.hoverColour
        else:
            self.colour = self.baseColour

        self.pointSelected = self.mouseHovering and self.layer.pygame.mouse.get_pressed()[0]

        if self.pointSelected:
            self.colour = self.pressedColour
            if self.action is not None and not self.actionRun:
                self.action()
                self.actionRun = True
        else:
            self.actionRun = False

    def display(self):
        self.boundingBox = self.layer.pygame.Rect(self.posX, self.posY, self.width, self.height)
        self.layer.pygame.draw.rect(self.layer.screen, self.colour, self.boundingBox, 0, self.roundedCorers)

        text_rect = self.font.get_rect(self.text)
        text_rect.center = (self.boundingBox.center[0] - self.textOffset[0], self.boundingBox.center[1] - self.textOffset[1])

        self.font.render_to(self.layer.screen, text_rect, self.text, (250, 250, 250))

class Label (UIElement):
    def __init__(self, layer, fontSize, pos, stick, text, colour, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)
        self.text = text

        self.font = layer.pygame.freetype.Font(layer.fontName, fontSize)
        self.textSize = self.font.get_rect(self.text).size
        self.colour = colour

        self.boundingBox = self.layer.pygame.Rect((self.posX - 10, self.posY - 10),  (self.textSize[0] + 20, self.textSize[1] + 20))

    def update(self):
        self.textSize = self.font.get_rect(self.text).size

    def display(self):
        self.font.render_to(self.layer.screen, (self.posX, self.posY), self.text, self.colour)

class Slider (UIElement): #Use label class for label
    def __init__(self, layer, fontSize, barColour, handleColour, pos, stick, size, length, valueRange, value = 0, action = None, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.barColour = barColour

        self.handleColour = handleColour
        self.selectedHandleColour = (handleColour[0] - (handleColour[0] * 0.4),
                                     handleColour[1] - (handleColour[1] * 0.4),
                                     handleColour[2] - (handleColour[2] * 0.4))
        self.displayColour = handleColour

        self.font = layer.pygame.freetype.Font(layer.fontName, fontSize)

        self.size = size
        self.length = length
        self.valueRange = valueRange

        self.mouseHovering = False
        self.handleX = ((self.length / (self.valueRange[1] - self.valueRange[0])) * value)  - (self.valueRange[0] / 2)
        self.handleSelected = False
        self.mouseDownLast = False
        self.handleSize = 0

        self.value = value
        self.action = action

    def update(self):
        mouseX, mouseY = self.layer.pygame.mouse.get_pos()
        self.handleSize = 10 * self.size
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
            elif self.posX >= mouseX:
                self.handleX = 0
            else:
                self.handleX = self.length

            self.value = (self.handleX / (self.length / (self.valueRange[1] - self.valueRange[0]))) + (self.valueRange[0])

        if not self.handleSelected:
            self.handleSelected = self.mouseHovering and self.layer.pygame.mouse.get_pressed()[0] and not self.mouseDownLast

        self.mouseDownLast = self.layer.pygame.mouse.get_pressed()[0]

    def display(self):
        bar = self.layer.pygame.Rect(self.posX, self.posY, self.length, 7 * self.size)
        self.layer.pygame.draw.rect(self.layer.screen, self.barColour, bar, 0, 100)
        self.font.render_to(self.layer.screen, (self.posX + self.length + 17, self.posY - 3), str(int(self.value)), self.barColour)

        self.layer.pygame.gfxdraw.aacircle(self.layer.screen, int(self.posX + self.handleX), int(self.posY + (7 * self.size) / 2), self.handleSize, self.displayColour)
        self.layer.pygame.gfxdraw.filled_circle(self.layer.screen, int(self.posX + self.handleX), int(self.posY + (7 * self.size) / 2), self.handleSize, self.displayColour)

    def updateValue(self, value):
        if self.valueRange[0] <= value <= self.valueRange[1]:
            self.value = value
            self.handleX = ((self.length / (self.valueRange[1] - self.valueRange[0])) * value) - (self.valueRange[0] / 2)

            if self.action is not None:
                self.action()

class Switch (UIElement): #Use label class for label
    def __init__(self, layer, colour, pos, stick, size, value = True, action = None, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.size = size
        self.value = value
        self.action = action

        self.barWidth = 0
        self.barHeight = 0

        self.colour = colour

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

        self.layer.pygame.gfxdraw.aacircle(self.layer.screen, int(self.posX + (self.barWidth / 4) + circleOffset), int(self.posY + (self.barHeight / 2)), int(9 * self.size), (20, 20, 20))
        self.layer.pygame.gfxdraw.filled_circle(self.layer.screen, int(self.posX + (self.barWidth / 4) + circleOffset), int(self.posY + (self.barHeight / 2)), int(9 * self.size), (20, 20, 20))

class Image(UIElement):
    def __init__(self, layer, pos, stick, imageDir, size, colour = None, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.imageDir = imageDir
        self.size = size
        self.colour = colour

        self.image = self.layer.pygame.image.load(self.imageDir).convert_alpha()
        self.image = self.layer.pygame.transform.scale_by(self.image, self.size)

        if self.colour is not None:
            self.image.fill(self.colour, special_flags = self.layer.pygame.BLEND_RGB_MAX)

    def display(self):
        if self.show:
            self.layer.screen.blit(self.image, (self.posX, self.posY))

    def manualUpdate(self):
        self.image = self.layer.pygame.image.load(self.imageDir).convert_alpha()
        self.image = self.layer.pygame.transform.scale_by(self.image, self.size)
        if self.colour is not None:
            self.image.fill(self.colour, special_flags = self.layer.pygame.BLEND_RGB_MAX)

class TextInput(UIElement):
    def __init__(self, layer, pos, stick, dimensions, placeholder = "", text = "", show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.width, self.height = dimensions
        self.placeholder = placeholder
        self.text = text
        self.font = layer.pygame.freetype.Font(layer.fontName, self.height - 20)

        self.show = show

    def update(self):
        pass

    def display(self):
        transparentSurface = self.layer.pygame.Surface((self.width, self.height), self.layer.pygame.SRCALPHA)
        self.layer.pygame.draw.rect(transparentSurface, (100, 100, 100, 100), (0, 0, self.width, self.height), border_radius = 15)
        self.layer.screen.blit(transparentSurface, (self.posX, self.posY))

        self.font.render_to(self.layer.screen, (self.posX + 20, self.posY + 10), self.text, (200, 200, 200))

class Accordion(UIElement):
    def __init__(self, layer, pos, stick, dimensions, elements, collapse = False, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.width, self.height = dimensions
        self.displayWidth, self.displayHeight = dimensions
        self.displayPosX, self.displayPosY = (self.posX, self.posY)
        self.collapsedSize = 50
        self.elements = elements
        self.collapse = collapse

        self.collapseButton = Button(layer, ((self.displayPosX - self.displayWidth) + 40, self.displayPosY - 10), stick, (30, 30), "", 15, (100, 100, 100), roundedCorners = 30, action = self.toggleCollapse)
        self.collapseImage = Image(layer, ((self.displayPosX - self.displayWidth) + 38, self.displayPosY - 12), stick, self.layer.directories["minus"], 1, (200, 200, 200))

        self.expandButton = Button(layer, ((self.displayPosX - self.displayWidth) + 40, (self.displayPosY - self.displayHeight) + 40), stick, (30, 30), "", 15, (100, 100, 100), roundedCorners = 30, action = self.toggleCollapse)
        self.expandImage = Image(layer, ((self.displayPosX - self.displayWidth) + 38, (self.displayPosY - self.displayHeight) + 38), stick, self.layer.directories["plus"], 1, (200, 200, 200))

    def update(self):
        if self.collapse:
            self.displayPosX, self.displayPosY = ((self.posX + self.width) - self.collapsedSize, (self.posY + self.height) - self.collapsedSize)

            self.collapseButton.show = False
            self.collapseImage.show = False
            self.expandButton.show = True
            self.expandImage.show = True

            self.displayHeight = self.collapsedSize
            self.displayWidth = self.collapsedSize

        else:
            self.displayPosX, self.displayPosY = (self.posX, self.posY)

            self.collapseButton.show = True
            self.collapseImage.show = True
            self.expandButton.show = False
            self.expandImage.show = False

            self.displayHeight = self.height
            self.displayWidth = self.width

        self.boundingBox = self.layer.pygame.Rect((self.displayPosX, self.displayPosY), (self.displayHeight, self.displayHeight))

    def display(self):
        transparentSurface = self.layer.pygame.Surface(self.boundingBox.size, self.layer.pygame.SRCALPHA)
        self.layer.pygame.draw.rect(transparentSurface, (50, 50, 50, 200), (0, 0, self.displayWidth, self.displayHeight), border_radius = 15)
        self.layer.screen.blit(transparentSurface, (self.displayPosX, self.displayPosY))

    def toggleCollapse(self):
        self.collapse = not self.collapse
        for element in self.elements:
            element.show = not self.collapse

class Message(UIElement):
    def __init__(self, layer, title, message, button1Text, button1Action, button1Colour, button2Text = None, button2Action = None, button2Colour = None, show = True, layerIndex = -1):
        super().__init__(layer, (0, 0), "", show, layerIndex)

        self.message = message
        self.title = title

        self.button1Text = button1Text
        self.button1Action = button1Action
        self.button1Colour = button1Colour

        self.button2Text = button2Text
        self.button2Action = button2Action
        self.button2Colour = button2Colour

        self.greyColour = (120, 120, 120)
        self.redColour = (95, 25, 25)

        self.width = 400
        self.height = 150

        self.posX = (self.layer.screenWidth / 2) - (self.width / 2)
        self.posY = (self.layer.screenHeight / 2) - (self.height / 2)

        self.boundingBox = self.layer.pygame.Rect(self.posX, self.posY, self.width, self.height)

        self.messageFont = layer.pygame.freetype.Font(layer.fontName, 15)
        self.titleFont = layer.pygame.freetype.Font(layer.fontName, 25)

        self.messageSize = self.messageFont.get_rect(self.message).size
        self.messageBoundingBox = self.layer.pygame.Rect((self.posX, self.posY), (self.messageSize[0], self.messageSize[1]))
        self.messageBoundingBox.center = self.boundingBox.center

        self.titleSize = self.titleFont.get_rect(self.title).size
        self.titleBoundingBox = self.layer.pygame.Rect((self.posX, self.posY), (self.titleSize[0], self.titleSize[1]))
        self.titleBoundingBox.center = self.boundingBox.center

        self.closeButton = Button(layer, (self.posX + self.width - 40, self.posY + 10), "", (30, 30), "", 10, self.greyColour, action = self.close)
        self.closeImage = Image(layer, (self.posX + self.width - 38, self.posY + 12), "", self.layer.directories["cross"], 1, (200, 200, 200))

        if button2Text is None:
            centreButtonColour = self.greyColour
            if self.button1Colour == "red":
                centreButtonColour = self.redColour

            self.centreButton = Button(layer, (self.posX + 10, (self.posY + self.height) - 40), "", (self.width - 20, 30), button1Text, 15, centreButtonColour, action = lambda: button1Action(self))

        else:
            leftButtonColour = self.greyColour
            if self.button1Colour == "red":
                leftButtonColour = self.redColour

            rightButtonColour = self.greyColour
            if self.button2Colour == "red":
                rightButtonColour = self.redColour

            self.leftButton = Button(layer, (self.posX + 10, (self.posY + self.height) - 40), "", ((self.width / 2) - 20, 30), button1Text, 15, leftButtonColour, action = lambda: button1Action(self))
            self.rightButton = Button(layer, (self.posX + 10 + (self.width / 2), (self.posY + self.height) - 40), "",((self.width / 2) - 20, 30), button2Text, 15, rightButtonColour, action = lambda: button2Action(self))

    def display(self):
        self.layer.pygame.draw.rect(self.layer.screen, (70, 70, 70), (self.posX, self.posY, self.width, self.height), border_radius = 15)
        self.titleFont.render_to(self.layer.screen, (self.titleBoundingBox.centerx - (self.titleSize[0] / 2), self.posY + 20), self.title, (200, 200, 200))
        self.messageFont.render_to(self.layer.screen, (self.messageBoundingBox.centerx - (self.messageSize[0] / 2), self.posY + 60), self.message, (200, 200, 200))

    def close(self):
        if self.button2Text is None:
            self.layer.elements.remove(self.centreButton)
        else:
            self.layer.elements.remove(self.leftButton)
            self.layer.elements.remove(self.rightButton)

        self.layer.elements.remove(self.closeButton)
        self.layer.elements.remove(self.closeImage)
        self.layer.elements.remove(self)

class Layer:
    def __init__(self, name, number, screen, pygame, fontName, directories):
        self.name = name
        self.number = number
        self.elements = []

        self.directories = directories

        self.screen = screen
        self.pygame = pygame
        self.fontName = fontName

        self.offset = None

        self.screenWidth = 0
        self.screenHeight = 0

    def add(self, element):
        self.elements.insert(element.layerIndex, element)

    def display(self, screenWidth, screenHeight, offset = None):
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight
        self.offset = offset
        for element in self.elements:
            if element.show:
                element.posX, element.posY = element.stickyPos()
                element.posX, element.posY = element.offsetPos(offset)
                element.update()
                element.display()

    def mouseOnLayer(self, mousePos):
        boundingBoxes = [element.returnBoundingBox() for element in self.elements if element.show]
        hovering = False
        mouseX, mouseY = mousePos

        for box in boundingBoxes:
            hovering = hovering or ((box[0][0] < mouseX < box[1][0]) and (box[0][1] < mouseY < box[2][1]))

        return hovering

    def clear(self):
        self.elements = []
