from typing import List
from gandy.image_redrawing.smarter.actions.move_action import MoveAction
from gandy.image_redrawing.smarter.actions.move_push_action import MoveAndPushAction
from gandy.image_redrawing.smarter.actions.expand_aspect_action import ExpandAspectAction
from gandy.image_redrawing.smarter.actions.shrink_action import ShrinkAction
from gandy.image_redrawing.smarter.actions.merge_text_action import MergeTextAction

MOVE_PCT = 0.01

general_adjustments: List[MoveAction] = [
    # Only move.
    MoveAction(offset_pct=[MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="l", action_name="MoveRight"),
    MoveAction(offset_pct=[-MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="r", action_name="MoveLeft"),
    MoveAction(offset_pct=[0, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="u", action_name="MoveDown"),
    MoveAction(offset_pct=[0, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="d", action_name="MoveUp"),
    # Move and push.
    MoveAndPushAction(offset_pct=[MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="l", action_name="PushRight"),
    MoveAndPushAction(offset_pct=[-MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="r", action_name="PushLeft"),
    MoveAndPushAction(offset_pct=[0, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="u", action_name="PushDown"),
    MoveAndPushAction(offset_pct=[0, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="d", action_name="PushUp"),
    # Diagonal move and move+push.
    MoveAction(offset_pct=[MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="lu", action_name="MoveDownRight"),
    MoveAndPushAction(offset_pct=[MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="lu", action_name="PushDownRight"),
    MoveAction(offset_pct=[-MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ru", action_name="MoveDownLeft"),
    MoveAndPushAction(offset_pct=[-MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ru", action_name="PushDownLeft"),
    MoveAction(offset_pct=[-MOVE_PCT, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="rd", action_name="MoveUpLeft"),
    MoveAndPushAction(offset_pct=[-MOVE_PCT, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="rd", action_name="PushUpLeft"),
    MoveAction(offset_pct=[MOVE_PCT, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ld", action_name="MoveUpRight"),
    MoveAndPushAction(offset_pct=[MOVE_PCT, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ld", action_name="PushUpRight"),
]

ACTIONS: List[MoveAction] = [
    # Stackables.
    ExpandAspectAction(stackable=True),
    *general_adjustments,
    # Last measures.
    ShrinkAction(shrink_factor=0.975, min_font_val=10, max_iterations=3, stackable=True),
    *general_adjustments,
    ShrinkAction(shrink_factor=0.975, min_font_val=10, max_iterations=3, stackable=True),
    *general_adjustments,
    ShrinkAction(shrink_factor=0.95, min_font_val=10, max_iterations=3, stackable=True),
    *general_adjustments,
    # Stackables.
    ExpandAspectAction(stackable=True),
    # A true final ditch measure!
    MergeTextAction(shrink_factor=0.8, min_font_val=2, max_iterations=5),
]