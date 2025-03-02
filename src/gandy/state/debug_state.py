class DebugState:
    def __init__(self) -> None:
        self.debug = False
        self.debug_redraw = False
        self.debug_dump_task5 = False
        self.debug_dump_task1 = False
        self.debug_dump_task3_ocr = False

        self.metadata = {}

    def set_debug(self, d: bool):
        self.debug = d


debug_state = DebugState()