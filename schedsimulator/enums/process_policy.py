from enum import Enum, auto

from enum import Enum

class Policy(Enum):
    """
    Linux scheduling policies, matching sched.h. These are the exact numbers used in sched.h in the linux kernel.
    Ordered by priority from highest (SCHED_DEADLINE) to lowest (SCHED_IDLE).
    """

    SCHED_DEADLINE = 6
    """Highest priority. Deadline-based real-time scheduling using EDF. Separate scheduler class."""

    SCHED_FIFO = 1
    """Real-time scheduler. First-In, First-Out. Tasks run until they yield or are preempted."""

    SCHED_RR = 2
    """Real-time scheduler. Round-Robin with timeslice. Lower than FIFO."""

    SCHED_OTHER = 0
    """Default fair scheduler (CFS). Normal interactive processes."""

    SCHED_BATCH = 3
    """CFS-based. For non-interactive batch workloads with lower priority."""

    SCHED_IDLE = 5
    """CFS-based. Runs only when no other tasks are runnable. Lowest priority."""

    # --- Helper Methods ---

    def is_deadline(self) -> bool:
        """True if the policy is SCHED_DEADLINE (highest priority, separate class)."""
        return self == Policy.SCHED_DEADLINE

    def is_realtime(self) -> bool:
        """True if the policy is in the real-time scheduler class (FIFO or RR)."""
        return self in {Policy.SCHED_FIFO, Policy.SCHED_RR}

    def is_cfs(self) -> bool:
        """True if the policy is handled by the CFS (OTHER or BATCH, )."""
        return self in {Policy.SCHED_OTHER, Policy.SCHED_BATCH}

    def is_idle(self) -> bool:
        return self == Policy.SCHED_IDLE