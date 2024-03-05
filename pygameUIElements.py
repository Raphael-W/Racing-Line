class Button:
    def __init__(self, screen, pos, dimensions, text, action):
        self.screen = screen
        self.pos = pos
        self.dimensions = dimensions
        self.text = text
        self.action = action

class Label:
    def __init__(self, screen, pos, size, text):
        self.screen = screen
        self.pos = pos
        self.size = size
        self.text = text

class Slider: #Use label class for label
    def __init__(self, screen, pos, size, length, valueRange, text, localLabelPos, value = 0, action = None):
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
    def __init__(self, screen, pos, size, text, localLabelPos, value = False, action = None):
        self.screen = screen
        self.pos = pos
        self.size = size
        self.text = text
        self.localLabelPos = localLabelPos

        self.value = value
        self.action = action