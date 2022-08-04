class Button:
    def __init__(self, label):
        self.label = label
    
    def set_action(self, action):
        self.action = action

buttons = []
labels = ["Label 1", "Label 2", "Label 3"]

for label in labels:
    button = Button(label)
    button.set_action(lambda: print(button.label))
    buttons.append(button)

for button in buttons:
    button.action()

# Output:

# Label 3
# Label 3
# Label 3

# Desired output:

# Label 1
# Label 2
# Label 3
