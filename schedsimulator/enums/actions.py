from enum import IntEnum

class Action(IntEnum):
    INCREASE_INTERACTIVE = 0
    DECREASE_INTERACTIVE = 1
    INCREASE_CPU = 2
    DECREASE_CPU = 3
    RESET_ALL = 4
    PRIORITIZE_INTERACTIVE = 5  # New compound action
