class Action:
    def __init__(self, command, params, ID):
        self.command = command
        self.params = params
        self.ID = ID

class Stack:
    def __init__(self):
        self.data = []

    def push(self, item):
        self.data.append(item)

    def pop(self):
        return self.data.pop()

    def peak(self):
        return self.data[-1]

    def clear(self):
        self.data.clear()

    def __len__(self):
        return len(self.data)

    def __str__(self):
        outputText = f"{'COMMAND': ^20}|{'PARAMETERS': ^60}|{'ID': ^10}\n"
        for i in range(len(self)):
            outputText += f"{self.data[i].command: ^20}|"
            outputText += f"{str(self.data[i].params): ^60}|"
            outputText += f"{str(self.data[i].ID): ^10}\n"
        outputText += '\n'
        return outputText

class History:
    def __init__(self):
        self.undoStack = Stack()
        self.redoStack = Stack()
        self.currentActionID = 0

    def addAction(self, command, params, group = False):
        if not group:
            self.currentActionID += 1

        action = Action(command, params, self.currentActionID)
        self.undoStack.push(action)
        self.redoStack.clear()

    def undo(self):
        if len(self.undoStack) > 0:
            actions = [self.undoStack.pop()]
            while len(self.undoStack) > 0:
                if self.undoStack.peak().ID == actions[0].ID:
                    actions.append(self.undoStack.pop())
                else:
                    break

            [self.redoStack.push(action) for action in actions]
            return actions
        return []

    def redo(self):
        if len(self.redoStack) > 0:
            actions = [self.redoStack.pop()]
            while len(self.redoStack) > 0:
                if self.redoStack.peak().ID == actions[0].ID:
                    actions.append(self.redoStack.pop())
                else:
                    break

            [self.undoStack.push(action) for action in actions]
            return actions
        return []
