class BaseAction:
    def __init__(self, action_name: str):
        self.iterations_left = 30
        self.action_name = action_name


def hash_text(text: str):
    # For debugging purposes.
    return text
    # return hash(text)
