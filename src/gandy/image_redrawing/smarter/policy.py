from typing import List
from gandy.image_redrawing.smarter.actions.move_action import MoveAction
from gandy.image_redrawing.smarter.actions.move_push_action import MoveAndPushAction
from gandy.image_redrawing.smarter.actions.expand_aspect_action import ExpandAspectAction
from gandy.image_redrawing.smarter.actions.shrink_action import ShrinkAction
from gandy.image_redrawing.smarter.actions.merge_text_action import MergeTextAction

MOVE_PCT = 0.01

SLIGHT_MOVE_ITERATIONS = 8
LARGE_MOVE_ITERATIONS = 30

def basic_movements(iterations: int):
    return [
        # Only move.
        MoveAction(offset_pct=[MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="l", action_name="MoveRight", max_iterations=iterations),
        MoveAction(offset_pct=[-MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="r", action_name="MoveLeft", max_iterations=iterations),
        MoveAction(offset_pct=[0, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="u", action_name="MoveDown", max_iterations=iterations),
        MoveAction(offset_pct=[0, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="d", action_name="MoveUp", max_iterations=iterations),
        # Push others and move self.
        MoveAndPushAction(offset_pct=[MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="l", action_name="PushRight", max_iterations=iterations),
        MoveAndPushAction(offset_pct=[-MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="r", action_name="PushLeft", max_iterations=iterations),
        MoveAndPushAction(offset_pct=[0, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="u", action_name="PushDown", max_iterations=iterations),
        MoveAndPushAction(offset_pct=[0, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="d", action_name="PushUp", max_iterations=iterations),
    ]

def diagonal_movements(iterations: int):
    return [
        MoveAction(offset_pct=[MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="lu", action_name="MoveDownRight", max_iterations=iterations),
        MoveAndPushAction(offset_pct=[MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="lu", action_name="PushDownRight", max_iterations=iterations),
        MoveAction(offset_pct=[-MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ru", action_name="MoveDownLeft", max_iterations=iterations),
        MoveAndPushAction(offset_pct=[-MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ru", action_name="PushDownLeft", max_iterations=iterations),
        MoveAction(offset_pct=[-MOVE_PCT, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="rd", action_name="MoveUpLeft", max_iterations=iterations),
        MoveAndPushAction(offset_pct=[-MOVE_PCT, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="rd", action_name="PushUpLeft", max_iterations=iterations),
        MoveAction(offset_pct=[MOVE_PCT, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ld", action_name="MoveUpRight", max_iterations=iterations),
        MoveAndPushAction(offset_pct=[MOVE_PCT, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ld", action_name="PushUpRight", max_iterations=iterations),
    ]

general_adjustments: List[MoveAction] = [
    *basic_movements(SLIGHT_MOVE_ITERATIONS),
    *diagonal_movements(SLIGHT_MOVE_ITERATIONS),
]

general_adjustments_large: List[MoveAction] = [
    *basic_movements(LARGE_MOVE_ITERATIONS),
    *diagonal_movements(LARGE_MOVE_ITERATIONS),
]

ACTIONS: List[MoveAction] = [
    # Stackables.
    ExpandAspectAction(stackable=True),
    *general_adjustments,
    # Last measures.
    ShrinkAction(shrink_factor=0.975, min_font_val=10, max_iterations=3, stackable=True, only_on_failure=True),
    *general_adjustments,
    ShrinkAction(shrink_factor=0.975, min_font_val=10, max_iterations=3, stackable=True, only_on_failure=True),
    *general_adjustments,
    ShrinkAction(shrink_factor=0.95, min_font_val=10, max_iterations=3, stackable=True, only_on_failure=True),
    *general_adjustments_large,
    # Stackables.
    ExpandAspectAction(stackable=True),
    # A true final ditch measure!
    MergeTextAction(shrink_factor=0.9, min_font_val=2, max_iterations=5),
]