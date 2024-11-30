from gandy.image_redrawing.smarter.text_box import TextBox
from gandy.image_redrawing.smarter.image_fonts import print_spam
from PIL import Image
from typing import List

class Action():
    def __init__(self, stackable: bool = False, action_name: str = "UnknownAction", max_iterations: int = 30, only_on_failure: bool = False) -> None:
        self.stackable = stackable
        self.only_on_failure = only_on_failure # For stackable actions only.

        self.action_name = action_name

        self.max_iterations = max_iterations
    
    def action_process(self, time_left: int, candidate: TextBox, others: List[TextBox], img: Image, original: TextBox):
        return candidate, others
    
    def fatal_error(self, candidate: TextBox, others: List[TextBox], img: Image, prev_candidate: TextBox):
        pass
    
    def non_fatal_error(self, candidate: TextBox, others: List[TextBox], img: Image):
        pass

    def begin(self,  candidate: TextBox, others: List[TextBox], img: Image):
        return self.process(self.max_iterations, candidate, others, img, original=candidate, original_others=others, iterations_done=1)

    def process(self, time_left: int, candidate: TextBox, others: List[TextBox], img: Image, original: TextBox, original_others: List[TextBox], iterations_done: int, **kwargs):
        print_spam(f'({self.action_name}) PROCESSING for BOX "{candidate.simple()}" with TimeLeft={time_left}')

        new_candidate, new_others = self.action_process(time_left, candidate, others, img, original, iterations_done, **kwargs)

        return self.validate(time_left, new_candidate, new_others, img, original, original_others, iterations_done=iterations_done, prev_candidate=candidate)

    def validate(self, time_left: int, candidate: TextBox, others: List[TextBox], img: Image, original: TextBox, original_others: List[TextBox], iterations_done: int, prev_candidate: TextBox, *args, **kwargs):
        print_spam('Validating CURRENT:')
        print_spam(candidate)
        print_spam('Validating OTHERS:')
        for o in others:
            print_spam(o)
        if time_left <= 0 or self.fatal_error(candidate, others, img, prev_candidate):
            return self.fail(candidate, others, original, original_others, prev_candidate)
        else:
            non_fatal_payload = self.non_fatal_error(candidate, others, img)

            if non_fatal_payload != False:
                return self.process(time_left - 1, candidate, others, img, original, original_others, iterations_done=(iterations_done + 1), non_fatal_payload=non_fatal_payload)
            else:
                return self.success(candidate, others)
    
    def fail(self, candidate: TextBox, others: List[TextBox], original: TextBox, original_others: List[TextBox], prev_candidate: TextBox):
        print_spam(f'({self.action_name}) FAILED for BOX "{candidate.simple()}"')

        # NOTE: Currently always returns others, which could be mutated.
        # Make sure to change this if we use other stackable actions that actually mutate other boxes.
        if self.stackable:
            return prev_candidate, others, False
        return original, original_others, False
    
    def success(self, candidate: TextBox, others: List[TextBox]):
        print_spam(f'({self.action_name}) SUCCEEDED for BOX "{candidate.simple()}"')

        return candidate, others, True