# TODO Make a PCB status for linux as well.
# TODO MAke the data for the process simular to linux.
from enum import Enum


class TaskStatus(Enum):
    NEW = 0
    READY = 1
    EXIT = 2
    BLOCKED = 3
    RUNNING = 4
