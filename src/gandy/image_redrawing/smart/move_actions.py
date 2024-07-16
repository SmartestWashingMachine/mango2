from gandy.image_redrawing.smart.move_action import MoveAction
from gandy.image_redrawing.smart.move_and_push_action import MoveAndPushAction
from gandy.image_redrawing.smart.utils.expand_box import expand_box
from gandy.image_redrawing.smart.constants import EXPAND_FACTOR


class MoveToRight(MoveAction):
    @classmethod
    def attempt(cls, box, *args, **kwargs):
        candidate = lambda b: expand_box(b, right=EXPAND_FACTOR, image=kwargs["img"])
        reject_action = cls.reject(
            overflow_direction="r"
        )  # It can no longer move to the right if it overflows to the right side of the image.

        return MoveAction(action_name="Move Right").attempt(
            box=box,
            make_candidate=candidate,
            reject_action=reject_action,
            overflow_fail_direction="l",  # It can keep going to the right if it overflows to the left side of the image.
            *args,
            **kwargs,
        )


class MoveToLeft(MoveAction):
    @classmethod
    def attempt(cls, box, *args, **kwargs):
        candidate = lambda b: expand_box(b, left=EXPAND_FACTOR, image=kwargs["img"])
        reject_action = cls.reject(overflow_direction="l")

        return MoveAction(action_name="Move Left").attempt(
            box=box,
            make_candidate=candidate,
            reject_action=reject_action,
            overflow_fail_direction="r",
            *args,
            **kwargs,
        )


class MoveToDown(MoveAction):
    @classmethod
    def attempt(cls, box, *args, **kwargs):
        candidate = lambda b: expand_box(b, down=EXPAND_FACTOR, image=kwargs["img"])
        reject_action = cls.reject(overflow_direction="d")

        return MoveAction(action_name="Move Down").attempt(
            box=box,
            make_candidate=candidate,
            reject_action=reject_action,
            overflow_fail_direction="u",
            *args,
            **kwargs,
        )


class MoveToUp(MoveAction):
    @classmethod
    def attempt(cls, box, *args, **kwargs):
        candidate = lambda b: expand_box(b, up=EXPAND_FACTOR, image=kwargs["img"])
        reject_action = cls.reject(overflow_direction="u")

        return MoveAction(action_name="Move Up").attempt(
            box=box,
            make_candidate=candidate,
            reject_action=reject_action,
            overflow_fail_direction="d",
            *args,
            **kwargs,
        )


class MoveAndPushToRight(MoveAndPushAction):
    @classmethod
    def attempt(cls, box, *args, **kwargs):
        candidate = lambda b: expand_box(b, right=EXPAND_FACTOR, image=kwargs["img"])
        reject_action = cls.reject(overflow_direction="r")

        return MoveAndPushAction(action_name="Move & Push Right").attempt(
            box=box,
            make_candidate=candidate,
            reject_action=reject_action,
            overflow_fail_direction="l",
            *args,
            **kwargs,
        )


class MoveAndPushToLeft(MoveAndPushAction):
    @classmethod
    def attempt(cls, box, *args, **kwargs):
        candidate = lambda b: expand_box(b, left=EXPAND_FACTOR, image=kwargs["img"])
        reject_action = cls.reject(overflow_direction="l")
        return MoveAndPushAction(action_name="Move & Push Left").attempt(
            box=box,
            make_candidate=candidate,
            reject_action=reject_action,
            overflow_fail_direction="r",
            *args,
            **kwargs,
        )
