class Button:
    def __init__(self, screen, pygame, pos, colour, dimensions, text, font, action):
        self.screen = screen
        self.pygame = pygame
        self.font = font

        self.posX = pos[0]
        self.posY = pos[1]
        self.colour = colour
        self.width = dimensions[0]
        self.height = dimensions[1]
        self.text = text
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

        rectangle = self.pygame.Rect(self.posX, self.posY, self.width, self.height)
        self.pygame.draw.rect(self.screen, self.colour, rectangle, 0, 10)

        text_rect = self.font.get_rect(self.text, size = 18)
        text_rect.center = rectangle.center

        self.font.render_to(self.screen, text_rect, self.text, (250, 250, 250))

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