class DebugState:
    def __init__(self) -> None:
        self.debug = False

    def set_debug(self, d: bool):
        self.debug = d


debug_state = DebugState()