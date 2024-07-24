import time
class UIElement:
    def __init__(self, layer, pos, stick, show = True, layerIndex = -1):
        self.contextualPosX = pos[0]
        self.contextualPosY = pos[1]

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

    def alwaysUpdate(self):
        pass

    def display(self):
        pass

    def returnBoundingBox(self):
        return self.boundingBox.topleft, self.boundingBox.topright, self.boundingBox.bottomleft, self.boundingBox.bottomright

    def updateContextualPos(self):
        contextualPosX = self.posX
        contextualPosY = self.posY

        #Offset position
        offsetX, offsetY = self.layer.offset

        contextualPosX = (((contextualPosX + (self.boundingBox.size[0] / 2)) * self.layer.zoom) - (self.boundingBox.size[0] / 2) + offsetX)
        contextualPosY = (((contextualPosY + (self.boundingBox.size[1] / 2)) * self.layer.zoom) - (self.boundingBox.size[1] / 2) + offsetY)

        #Apply stickiness to position
        vertValid = not (("n" in self.stick) and ("s" in self.stick))
        horValid = not (("e" in self.stick) and ("w" in self.stick))
        charValid = all([True for char in self.stick if char in ["n", "e", "s", "w"]])

        horStick = None
        vertStick = None
        for char in self.stick:
            if char in ["n", "s"]:
                vertStick = char
            elif char in ["e", "w"]:
                horStick = char

        if vertValid and horValid and charValid and (len(self.stick) > 0):
            if horStick == "e":
                contextualPosX = self.layer.screenWidth - self.posX

            if vertStick == "s":
                contextualPosY = self.layer.screenHeight - self.posY

        self.contextualPosX, self.contextualPosY = contextualPosX, contextualPosY

    def close(self):
        if self in self.layer.elements:
            self.layer.elements.remove(self)

class Button (UIElement):
    def __init__(self, layer, pos, stick, dimensions, text, fontSize, colour, textOffset = (0, 0), roundedCorners = 10, action = None, show = True, disabled = False, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)
        self.width = dimensions[0]
        self.height = dimensions[1]
        self.boundingBox = layer.pygame.Rect(self.posX, self.posY, self.width, self.height)
        self.roundedCorers = roundedCorners

        self.text = text
        self.textOffset = textOffset
        self.font = layer.pygame.freetype.Font(layer.fontName, fontSize)

        self.action = action

        self.stepBeforeClick = False
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

        self.disabled = disabled

    def update(self):
        self.updateContextualPos()

        if not self.disabled:
            mousePos = self.layer.pygame.mouse.get_pos()
            self.mouseHovering = (((self.contextualPosX + self.width / 2) + ((self.width / 2) + 2) > mousePos[0] > (self.contextualPosX + self.width / 2) - ((self.width / 2) + 2)) and
                                  ((self.contextualPosY + self.height / 2) + ((self.height / 2) + 2) > mousePos[1] > (self.contextualPosY + self.height / 2) - ((self.height / 2) + 2)))

            if self.mouseHovering:
                self.colour = self.hoverColour
            else:
                self.colour = self.baseColour

            self.pointSelected = self.mouseHovering and self.layer.pygame.mouse.get_pressed()[0]
            if self.pointSelected:
                self.colour = self.pressedColour

            if self.pointSelected and self.stepBeforeClick:
                if self.action is not None and not self.actionRun:
                    self.action()
                    self.actionRun = True
            else:
                self.actionRun = False

            self.stepBeforeClick = self.mouseHovering and not(self.layer.pygame.mouse.get_pressed()[0])

        else:
            self.colour = self.pressedColour

    def display(self):
        self.boundingBox = self.layer.pygame.Rect(self.contextualPosX, self.contextualPosY, self.width, self.height)
        self.layer.pygame.draw.rect(self.layer.screen, self.colour, self.boundingBox, 0, self.roundedCorers)

        text_rect = self.font.get_rect(self.text)
        text_rect.center = (self.boundingBox.center[0] - self.textOffset[0], self.boundingBox.center[1] - self.textOffset[1])

        self.font.render_to(self.layer.screen, text_rect, self.text, (250, 250, 250))

class Label (UIElement):
    def __init__(self, layer, fontSize, pos, stick, text, colour, bold = False, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)
        self.text = text

        self.font = layer.pygame.freetype.Font(layer.fontName, fontSize)
        self.font.strong = bold

        self.textSize = self.font.get_rect(self.text).size
        self.colour = colour

    def update(self):
        self.updateContextualPos()

        self.textSize = self.font.get_rect(self.text).size
        self.boundingBox = self.layer.pygame.Rect((self.contextualPosX - 10, self.contextualPosY - 10), (self.textSize[0] + 20, self.textSize[1] + 20))

    def display(self):
        self.font.render_to(self.layer.screen, (self.contextualPosX, self.contextualPosY), self.text, self.colour)

class Slider (UIElement):
    def __init__(self, layer, fontSize, barColour, handleColour, pos, stick, size, length, valueRange, value = 0, action = None, finishedUpdatingAction = None, show = True, disabled = False, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.barColour = barColour
        self.displayBarColour = self.barColour

        self.handleColour = handleColour
        self.selectedHandleColour = (handleColour[0] - (handleColour[0] * 0.4),
                                     handleColour[1] - (handleColour[1] * 0.4),
                                     handleColour[2] - (handleColour[2] * 0.4))
        self.displayColour = handleColour

        self.font = layer.pygame.freetype.Font(layer.fontName, fontSize)

        self.size = size
        self.length = length
        self.valueRange = valueRange
        self.value = value
        if not (valueRange[0] <= value <= valueRange[1]): self.value = valueRange[0]

        self.mouseHovering = False
        self.handleX = (self.length / (self.valueRange[1] - self.valueRange[0])) * (self.value - self.valueRange[0])
        self.handleSelected = False
        self.handleSelectedLast = False
        self.mouseDownLast = False
        self.handleSize = int(10 * self.size)


        self.initialValue = value
        self.action = action
        self.finishedUpdatingAction = finishedUpdatingAction

        self.show = show
        self.disabled = disabled

    def update(self):
        self.updateContextualPos()

        if not self.disabled:
            mouseX, mouseY = self.layer.pygame.mouse.get_pos()
            self.handleSize = int(10 * self.size)
            self.boundingBox = self.layer.pygame.Rect(self.contextualPosX + self.handleX - self.handleSize, self.contextualPosY - (self.handleSize * 0.75), self.handleSize * 2, self.handleSize * 2)
            self.mouseHovering = (((self.contextualPosX + self.handleX) + (self.handleSize + 2) > mouseX > (self.contextualPosX + self.handleX) - (self.handleSize + 2)) and
                                  (self.contextualPosY + (self.handleSize + 2) > mouseY > self.contextualPosY - (self.handleSize + 2)))

            self.displayBarColour = self.barColour
            if self.mouseHovering or self.handleSelected:
                self.displayColour = self.selectedHandleColour
            else:
                self.displayColour = self.handleColour

            if not self.layer.pygame.mouse.get_pressed()[0]:
                self.handleSelected = False

            if self.handleSelected:
                if self.action is not None:
                    self.action(self.value)

                if self.contextualPosX < mouseX < (self.contextualPosX + self.length):
                    self.handleX = mouseX - self.contextualPosX
                elif self.contextualPosX >= mouseX:
                    self.handleX = 0
                else:
                    self.handleX = self.length

                self.value = (self.handleX / (self.length / (self.valueRange[1] - self.valueRange[0]))) + (self.valueRange[0])

            if not self.handleSelected:
                self.handleSelected = self.mouseHovering and self.layer.pygame.mouse.get_pressed()[0] and not self.mouseDownLast

            if self.handleSelected and not self.handleSelectedLast:
                self.initialValue = self.value

            if not self.handleSelected and self.handleSelectedLast:
                if self.finishedUpdatingAction is not None:
                    self.finishedUpdatingAction(self.initialValue, self)

            self.mouseDownLast = self.layer.pygame.mouse.get_pressed()[0]
            self.handleSelectedLast = self.handleSelected
        else:
            self.displayBarColour = (120, 120, 120)
            self.displayColour = (46, 80, 94)

    def display(self):
        bar = self.layer.pygame.Rect(self.contextualPosX, self.contextualPosY, self.length, int(7 * self.size))
        self.layer.pygame.draw.rect(self.layer.screen, self.displayBarColour, bar, 0, 100)
        self.font.render_to(self.layer.screen, (self.contextualPosX + self.length + 17, self.contextualPosY - 3), str(int(self.value)), self.displayBarColour)

        self.layer.pygame.gfxdraw.aacircle(self.layer.screen, int(self.contextualPosX + self.handleX), int(self.contextualPosY + (int(7 * self.size)) / 2), self.handleSize, self.displayColour)
        self.layer.pygame.gfxdraw.filled_circle(self.layer.screen, int(self.contextualPosX + self.handleX), int(self.contextualPosY + (int(7 * self.size)) / 2), self.handleSize, self.displayColour)

    def updateValue(self, value, update = True):
        if self.valueRange[0] <= value <= self.valueRange[1]:
            self.value = value
            self.handleX = (self.length / (self.valueRange[1] - self.valueRange[0])) * (value - self.valueRange[0])

            if self.action is not None and update:
                self.action(self.value)

class Switch (UIElement):
    def __init__(self, layer, pos, stick, size, value = True, action = None, show = True, disabled = False, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.size = size
        self.value = value
        self.action = action
        self.disabled = disabled

        self.barWidth = 0
        self.barHeight = 0

        self.trueColour = (41, 66, 43)
        self.falseColour = (66, 41, 41)
        self.colour = (0, 0, 0)

        self.handleColour = (20, 20, 20)
        self.handleDisplayColour = (20, 20, 20)

        self.mouseHovering = False
        self.pointSelected = False
        self.mouseDownLast = False

    def update(self):
        self.updateContextualPos()

        self.barWidth = 55 * self.size
        self.barHeight = 25 * self.size
        mouseX, mouseY = self.layer.pygame.mouse.get_pos()

        self.mouseHovering = ((self.contextualPosX + self.barWidth > mouseX > self.contextualPosX) and (self.contextualPosY + self.barHeight > mouseY > self.contextualPosY)) and not self.disabled

        if self.mouseHovering:
            self.pointSelected = self.mouseHovering and self.layer.pygame.mouse.get_pressed()[0] and not self.mouseDownLast

        if self.pointSelected:
            self.value = not self.value
            self.pointSelected = False

            if self.action is not None:
                self.action()

        if self.value:
            self.colour = self.trueColour
            if self.mouseHovering:
                self.colour = (self.trueColour[0] - (self.trueColour[0] * 0.2), self.trueColour[1] - (self.trueColour[1] * 0.2), self.trueColour[1] - (self.trueColour[1] * 0.2))

            if self.disabled:
                self.handleDisplayColour = (32, 38, 32)
                self.colour = (42, 51, 43)
            else:
                self.handleDisplayColour = self.handleColour
                self.colour = self.trueColour
        else:
            self.colour = self.falseColour
            if self.mouseHovering:
                self.colour = (self.falseColour[0] - (self.falseColour[0] * 0.2), self.falseColour[1] - (self.falseColour[1] * 0.2), self.falseColour[1] - (self.falseColour[1] * 0.2))

            if self.disabled:
                self.handleDisplayColour = (43, 33, 33)
                self.colour = (54, 40, 40)
            else:
                self.handleDisplayColour = self.handleColour
                self.colour = self.falseColour

        self.mouseDownLast = self.layer.pygame.mouse.get_pressed()[0]

    def display(self):
        self.boundingBox = self.layer.pygame.Rect(self.contextualPosX, self.contextualPosY, self.barWidth, self.barHeight)
        self.layer.pygame.draw.rect(self.layer.screen, self.colour, self.boundingBox, 0, 100)

        if self.value:
            circleOffset = (self.barWidth / 2)
        else:
            circleOffset = 0

        self.layer.pygame.gfxdraw.aacircle(self.layer.screen, int(self.contextualPosX + (self.barWidth / 4) + circleOffset), int(self.contextualPosY + (self.barHeight / 2)), int(9 * self.size), self.handleDisplayColour)
        self.layer.pygame.gfxdraw.filled_circle(self.layer.screen, int(self.contextualPosX + (self.barWidth / 4) + circleOffset), int(self.contextualPosY + (self.barHeight / 2)), int(9 * self.size), self.handleDisplayColour)

class Image(UIElement):
    def __init__(self, layer, pos, stick, imageDir, size, colour = None, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.imageDir = imageDir
        self.size = size
        self.colour = colour

        self.angle = 0
        self.transformedImage = None
        self.transformedRect = None

        self.image = self.layer.pygame.image.load(self.imageDir).convert_alpha()
        self.boundingBox = self.image.get_rect()

    def update(self):
        self.updateContextualPos()
        self.transformedImage = self.image
        self.transformedImage = self.layer.pygame.transform.scale_by(self.transformedImage, self.size)
        self.transformedImage = self.layer.pygame.transform.rotate(self.transformedImage, (self.angle % 360))

        if self.colour is not None:
            self.transformedImage.fill(self.colour, special_flags = self.layer.pygame.BLEND_RGB_MAX)

        imageSize = self.getSize()
        self.transformedRect = self.transformedImage.get_rect(center = (self.contextualPosX + (imageSize[0] / 2), self.contextualPosY + (imageSize[1] / 2)))

    def display(self):
        if self.show:
            self.layer.screen.blit(self.transformedImage, self.transformedRect)

    def getSize(self):
        return self.boundingBox.size

    def updateImage(self, newDir):
        self.imageDir = newDir
        self.image = self.layer.pygame.image.load(self.imageDir).convert_alpha()
        self.boundingBox = self.image.get_rect()

class TextInput(UIElement):
    def __init__(self, layer, pos, stick, dimensions, fontSize, placeholder = "", text = "", suffix = "", characterWhitelist = (), enterAction = None, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.width, self.height = dimensions
        self.fontSize = fontSize
        self.placeholder = placeholder
        self.text = text
        self.suffix = suffix

        self.characterWhitelist = characterWhitelist
        self.font = layer.pygame.freetype.Font(layer.fontName, self.fontSize)
        self.enterAction = enterAction

        self.showTypingBar = True
        self.timeAtFlash = time.time()

        self.hovering = False
        self.selected = True

        self.cursorIndex = 0

        self.show = show

    def update(self):
        self.updateContextualPos()

        if self.selected:
            if (time.time() - self.timeAtFlash) >= 0.5:
                self.showTypingBar = not self.showTypingBar
                self.timeAtFlash = time.time()

        for letter in self.layer.events:
            if letter.type == 768: #int version of 'pygame.KEYDOWN'
                letterUni = letter.unicode
                if letterUni in self.characterWhitelist:

                    self.timeAtFlash = time.time()
                    self.showTypingBar = True

                    self.text = self.text[:self.cursorIndex] + letterUni + self.text[self.cursorIndex:]
                    self.cursorIndex += 1

                if letter.key == self.layer.pygame.K_BACKSPACE:
                    self.text = self.text[:self.cursorIndex - 1] + self.text[self.cursorIndex:]

                if letter.key == self.layer.pygame.K_RIGHT:
                    self.cursorIndex += 1

                if letter.key == self.layer.pygame.K_LEFT:
                    self.cursorIndex -= 1

                if letter.key == self.layer.pygame.K_RETURN:
                    if self.enterAction is not None:
                        self.enterAction(self.text)

    def display(self):
        transparentSurface = self.layer.pygame.Surface((self.width, self.height), self.layer.pygame.SRCALPHA)
        self.layer.pygame.draw.rect(transparentSurface, (100, 100, 100, 100), (0, 0, self.width, self.height), border_radius = 15)
        self.layer.screen.blit(transparentSurface, (self.contextualPosX, self.contextualPosY))

        if self.text == "":
            self.font.render_to(self.layer.screen, (self.contextualPosX + 10, self.contextualPosY + (self.height / 2) - (self.fontSize / 2)), self.placeholder, (150, 150, 150))
        else:
            self.font.render_to(self.layer.screen, (self.contextualPosX + 10, self.contextualPosY + (self.height / 2) - (self.fontSize / 2)), self.text + self.suffix, (200, 200, 200))

        if self.showTypingBar:
            if self.cursorIndex > (len(self.text)):
                self.cursorIndex = len(self.text)

            elif self.cursorIndex <= 0:
                self.cursorIndex = 0

            textWidth = self.font.get_rect(self.text[:self.cursorIndex]).width
            self.layer.pygame.draw.line(self.layer.screen, (200, 200, 200), (self.contextualPosX + 10 + textWidth, self.contextualPosY + 15), (self.contextualPosX + 10 + textWidth, self.contextualPosY - 15 + self.height), 2)

class Accordion(UIElement):
    def __init__(self, layer, pos, stick, dimensions, title, elements, collapse = False, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)

        self.width, self.height = dimensions
        self.displayWidth, self.displayHeight = dimensions
        self.collapsedSize = 50

        self.titleText = title
        self.titleLabel = Label(layer, 20, (0, 0), stick, self.titleText, (200, 200, 200))

        self.elements = elements + [self.titleLabel]
        self.collapse = collapse

        self.collapseButton = Button(layer, (0, 0), stick, (30, 30), "", 15, (100, 100, 100), roundedCorners = 30,
                                     action = self.toggleCollapse)
        self.collapseImage = Image(layer, (0, 0), stick, self.layer.directories["minus"], 1, colour = (200, 200, 200))
        self.expandImage = Image(layer, (0, 0), stick, self.layer.directories["plus"], 1, colour = (200, 200, 200))

    def update(self):
        self.updateContextualPos()

        if self.collapse:
            self.displayHeight = self.collapsedSize
            self.displayWidth = self.collapsedSize

            self.collapseImage.show = False
            self.expandImage.show = True

        else:
            self.displayHeight = self.height
            self.displayWidth = self.width

            self.collapseImage.show = True
            self.expandImage.show = False

        self.collapseImage.posX, self.collapseImage.posY = (self.posX + 38, (self.posY + self.displayHeight) - 12)
        self.expandImage.posX, self.expandImage.posY = (self.posX + 38, (self.posY + self.displayHeight) - 12)
        self.collapseButton.posX, self.collapseButton.posY = (self.posX + 40, (self.posY + self.displayHeight) - 10)

        self.titleLabel.text = self.titleText[:15]
        if len(self.titleText) > 15:
            self.titleLabel.text += "..."
        self.titleLabel.posX, self.titleLabel.posY = ((self.displayWidth / 2) + (self.titleLabel.textSize[0] / 2) + self.posX, self.displayHeight - 25 + self.posY)

        self.boundingBox = self.layer.pygame.Rect((self.contextualPosX - self.displayWidth, self.contextualPosY - self.displayHeight), (self.displayWidth, self.displayHeight))

    def display(self):
        transparentSurface = self.layer.pygame.Surface(self.boundingBox.size, self.layer.pygame.SRCALPHA)
        self.layer.pygame.draw.rect(transparentSurface, (50, 50, 50, 200), (0, 0, self.displayWidth, self.displayHeight), border_radius = 15)
        self.layer.screen.blit(transparentSurface, (self.contextualPosX - self.displayWidth, self.contextualPosY - self.displayHeight))

    def toggleCollapse(self):
        self.collapse = not self.collapse
        for element in self.elements:
            element.show = not self.collapse

class Message(UIElement):
    def __init__(self, layer, title, message, button1Text, button1Action, button1Colour, button2Text = None, button2Action = None, button2Colour = None, xAction = None, show = True, layerIndex = -1):
        super().__init__(layer, (0, 0), "", show, layerIndex)

        self.message = message
        self.title = title

        self.button1Text = button1Text
        self.button1Action = button1Action
        self.button1Colour = button1Colour

        self.button2Text = button2Text
        self.button2Action = button2Action
        self.button2Colour = button2Colour

        self.xAction = xAction

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

        self.closeButton = Button(layer, (self.posX + self.width - 40, self.posY + 10), "", (30, 30), "", 10,
                                  self.greyColour, action = self.closeButton)
        self.closeImage = Image(layer, (self.posX + self.width - 38, self.posY + 12), "", self.layer.directories["cross"], 1, colour = (200, 200, 200))

        if button2Text is None:
            centreButtonColour = self.greyColour
            if self.button1Colour == "red":
                centreButtonColour = self.redColour

            self.centreButton = Button(layer, (self.posX + 10, (self.posY + self.height) - 40), "",
                                       (self.width - 20, 30), button1Text, 15, centreButtonColour,
                                       action = lambda: button1Action(self))

        else:
            leftButtonColour = self.greyColour
            if self.button1Colour == "red":
                leftButtonColour = self.redColour

            rightButtonColour = self.greyColour
            if self.button2Colour == "red":
                rightButtonColour = self.redColour

            self.leftButton = Button(layer, (self.posX + 10, (self.posY + self.height) - 40), "",
                                     ((self.width / 2) - 20, 30), button1Text, 15, leftButtonColour,
                                     action = lambda: button1Action(self))
            self.rightButton = Button(layer, (self.posX + 10 + (self.width / 2), (self.posY + self.height) - 40), "",
                                      ((self.width / 2) - 20, 30), button2Text, 15, rightButtonColour,
                                      action = lambda: button2Action(self))

    def update(self):
        self.posX = (self.layer.screenWidth / 2) - (self.width / 2)
        self.posY = (self.layer.screenHeight / 2) - (self.height / 2)
        self.boundingBox = self.layer.pygame.Rect(self.posX, self.posY, self.width, self.height)

        self.messageBoundingBox = self.layer.pygame.Rect((self.posX, self.posY),(self.messageSize[0], self.messageSize[1]))
        self.messageBoundingBox.center = self.boundingBox.center

        self.titleBoundingBox = self.layer.pygame.Rect((self.posX, self.posY), (self.titleSize[0], self.titleSize[1]))
        self.titleBoundingBox.center = self.boundingBox.center

        self.closeButton.posX, self.closeButton.posY = (self.posX + self.width - 40, self.posY + 10)
        self.closeImage.posX, self.closeImage.posY = (self.posX + self.width - 38, self.posY + 12)

        if self.button2Text is None:
            self.centreButton.posX, self.centreButton.posY = (self.posX + 10, (self.posY + self.height) - 40)
        else:
            self.leftButton.posX, self.leftButton.posY = (self.posX + 10, (self.posY + self.height) - 40)
            self.rightButton.posX, self.rightButton.posY = (self.posX + 10 + (self.width / 2), (self.posY + self.height) - 40)

    def display(self):
        transparentSurface = self.layer.pygame.Surface((self.layer.screenWidth, self.layer.screenHeight), self.layer.pygame.SRCALPHA)
        self.layer.pygame.draw.rect(transparentSurface, (50, 50, 50, 200), (0, 0, self.layer.screenWidth, self.layer.screenHeight))
        self.layer.screen.blit(transparentSurface, (0, 0))

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

    def closeButton(self):
        if self.xAction is None:
            self.close()
        else:
            self.xAction()

class Dropdown(UIElement):
    def __init__(self, layer, pos, stick, dimensions, values, itemIndex, disabledIndexes = [], action = None, show = True, layerIndex = -1):
        super().__init__(layer, pos, stick, show, layerIndex)
        self.values = values
        self.index = itemIndex
        self.disabledIndexes = disabledIndexes

        self.action = action

        self.font = layer.pygame.freetype.Font(layer.fontName, 15)
        self.colour = (200, 200, 200)

        self.width, self.height = dimensions
        self.boundingBox = self.layer.pygame.Rect(pos, dimensions)

        self.dropdownIcon = Image(layer, (0, 0), "", self.layer.directories["down"], 1, (30, 30, 30), show)
        self.displayMenu = False

        self.mouseHovering = False
        self.hoveringItemIndex = None
        self.pointSelected = False
        self.stepBeforeClick = False
        self.noClickBefore = False

    def update(self):
        self.updateContextualPos()

        self.dropdownIcon.posX, self.dropdownIcon.posY = (self.contextualPosX + (self.width - 30), self.contextualPosY + (self.height / 2) - 13)

        mousePos = self.layer.pygame.mouse.get_pos()
        self.mouseHovering = (((self.contextualPosX + self.width / 2) + ((self.width / 2) + 2) > mousePos[0] >= (self.contextualPosX + self.width / 2) - ((self.width / 2) + 2)) and
                              ((self.contextualPosY + self.height / 2) + ((self.height / 2) + 0) > mousePos[1] >= (self.contextualPosY + self.height / 2) - ((self.height / 2) + 2)))

        if self.displayMenu: totalHeight = len(self.values) * 22 + self.height + 5
        else: totalHeight = self.height
        self.boundingBox = self.layer.pygame.Rect((self.contextualPosX, self.contextualPosY), (self.width, totalHeight))

        if self.mouseHovering:
            self.colour = (75, 75, 75)
        else:
            self.colour = (100, 100, 100)

        self.pointSelected = self.mouseHovering and self.layer.pygame.mouse.get_pressed()[0]
        if self.pointSelected and self.stepBeforeClick:
            self.displayMenu = not self.displayMenu
        elif self.displayMenu and self.layer.pygame.mouse.get_pressed()[0] and self.noClickBefore and not self.boundingBox.collidepoint(mousePos):
            self.displayMenu = False

        if self.displayMenu:
            self.dropdownIcon.angle = 180
            self.layer.overrideUpdateElements = [self]
        else:
            self.dropdownIcon.angle = 0
            self.layer.overrideUpdateElements = None


        if self.displayMenu:
            self.hoveringItemIndex = None
            currentIndex = 0
            for i in range(len(self.values) - 1):
                if i == self.index:
                    currentIndex += 1

                mouseOverItem = (((self.contextualPosX + self.width) > mousePos[0] >= self.contextualPosX) and
                                 (self.contextualPosY + ((i + 1) * 22) + self.height > mousePos[1] >= self.contextualPosY + (i * 22) + self.height))
                if mouseOverItem and (currentIndex not in self.disabledIndexes):
                    self.hoveringItemIndex = i
                    if self.layer.pygame.mouse.get_pressed()[0]:
                        self.index = currentIndex
                        self.displayMenu = False
                        if self.action is not None:
                            self.action(self.values[currentIndex])
                currentIndex += 1

        self.stepBeforeClick = self.mouseHovering and not(self.layer.pygame.mouse.get_pressed()[0])
        self.noClickBefore = not(self.layer.pygame.mouse.get_pressed()[0])

    def alwaysUpdate(self):
        self.dropdownIcon.show = self.show

    def display(self):
        if self.displayMenu:
            self.layer.pygame.draw.rect(self.layer.screen, (100, 100, 100), (self.contextualPosX, self.contextualPosY, self.width, (len(self.values) - 1) * 22 + self.height + 5), border_radius = 10)
            currentIndex = 0
            for i in range(len(self.values) - 1):
                if i == self.index:
                    currentIndex += 1

                if (i == self.hoveringItemIndex) and (currentIndex not in self.disabledIndexes):
                    self.layer.pygame.draw.rect(self.layer.screen, (75, 75, 75), (self.contextualPosX, self.contextualPosY + (i * 22) + self.height, self.width, 22), border_radius = 10)

                if currentIndex in self.disabledIndexes:
                    colour = (150, 150, 150)
                else:
                    colour = (200, 200, 200)
                self.font.render_to(self.layer.screen, (self.contextualPosX + 10, self.contextualPosY + self.height + (22 * i) + 5), str(self.values[currentIndex]), colour)
                currentIndex += 1

        self.layer.pygame.draw.rect(self.layer.screen, self.colour, (self.contextualPosX, self.contextualPosY, self.width, self.height), border_radius = 10)
        self.font.render_to(self.layer.screen, (self.contextualPosX + 10, self.contextualPosY + (self.height / 2) - 6), str(self.values[self.index]), (200, 200, 200))

    def getCurrent(self):
        return self.values[self.index]

class Layer:
    def __init__(self, screen, pygame, fontName, directories):
        self.elements = []
        self.overrideUpdateElements = None

        self.directories = directories

        self.screen = screen
        self.pygame = pygame
        self.fontName = fontName

        self.offset = (0, 0)
        self.zoom = 1

        self.screenWidth = 0
        self.screenHeight = 0

        self.events = []

    def add(self, element):
        insertIndex = element.layerIndex
        if insertIndex < 0:
            insertIndex = len(self.elements)

        self.elements.insert(insertIndex, element)

    def display(self, screenWidth, screenHeight, events, offset = (0, 0), zoom = 1):
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight
        self.offset = offset
        self.zoom = zoom
        self.events = events

        for element in self.elements:
            if element.show:
                if (self.overrideUpdateElements is not None and element in self.overrideUpdateElements) or (self.overrideUpdateElements is None):
                    element.update()
                element.display()
            element.alwaysUpdate()

    def mouseOnLayer(self, mousePos):
        boundingBoxes = [element.returnBoundingBox() for element in self.elements if element.show]
        hovering = False
        mouseX, mouseY = mousePos

        for box in boundingBoxes:
            hovering = hovering or ((box[0][0] < mouseX < box[1][0]) and (box[0][1] < mouseY < box[2][1]))

        return hovering

    def clear(self):
        self.elements = []
