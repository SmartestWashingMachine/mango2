from gandy.image_redrawing.smarter.text_box import TextBox
from PIL import Image
from typing import List

class Action():
    def __init__(self, stackable = False, action_name: str = "UnknownAction") -> None:
        self.stackable = stackable

        self.action_name = action_name
    
    def action_process(self, time_left: int, candidate: TextBox, others: List[TextBox], img: Image, original: TextBox):
        return candidate, others
    
    def fatal_error(self, candidate: TextBox, others: List[TextBox], img: Image):
        pass
    
    def non_fatal_error(self, candidate: TextBox, others: List[TextBox], img: Image):
        pass

    def begin(self, time_left: int, candidate: TextBox, others: List[TextBox], img: Image):
        return self.process(time_left, candidate, others, img, original=candidate, original_others=others, iterations_done=1)

    def process(self, time_left: int, candidate: TextBox, others: List[TextBox], img: Image, original: TextBox, original_others: List[TextBox], iterations_done: int):
        print(f'({self.action_name}) PROCESSING for BOX "{candidate.simple()}" with TimeLeft={time_left}')

        new_candidate, new_others = self.action_process(time_left, candidate, others, img, original, iterations_done)

        return self.validate(time_left, new_candidate, new_others, img, original, original_others, iterations_done=iterations_done)

    def validate(self, time_left: int, candidate: TextBox, others: List[TextBox], img: Image, original: TextBox, original_others: List[TextBox], iterations_done: int, *args, **kwargs):
        print('Validating CURRENT:')
        print(candidate)
        print('Validating OTHERS:')
        for o in others:
            print(o)
        if time_left <= 0 or self.fatal_error(candidate, others, img):
            return self.fail(candidate, others, original, original_others)
        elif self.non_fatal_error(candidate, others, img):
            return self.process(time_left - 1, candidate, others, img, original, original_others, iterations_done=(iterations_done + 1))
        else:
            return self.success(candidate, others)
    
    def fail(self, candidate: TextBox, others: List[TextBox], original: TextBox, original_others: List[TextBox]):
        print(f'({self.action_name}) FAILED for BOX "{candidate.simple()}"')

        # NOTE: Currently always returns others, which could be mutated.
        # Make sure to change this if we use other stackable actions that actually mutate other boxes.
        if self.stackable:
            return candidate, others, False
        return original, original_others, False
    
    def success(self, candidate: TextBox, others: List[TextBox]):
        print(f'({self.action_name}) SUCCEEDED for BOX "{candidate.simple()}"')

        return candidate, others, True