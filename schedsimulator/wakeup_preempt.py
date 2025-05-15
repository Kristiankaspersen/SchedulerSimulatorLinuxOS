from schedsimulator.enqueue_task import enqueue_entity
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.globals import PREEMPT_SHORT
from schedsimulator.pick_next_task_fair import pick_eevdf
from schedsimulator.update_current import update_curr
from schedsimulator.utils import entity_eligible, entity_before


def check_preempt_wakeup_fair(cfs_rq, task):
    update_curr(cfs_rq)
    resched = False
    if task == cfs_rq.curr:
        return

    #se = curr  # or curr.se if you're using sched_entity objects
    #pse = task  # or task.se

    if do_preempt_short(cfs_rq, task, cfs_rq.curr):
        cancel_protect_slice(cfs_rq.curr)

    if pick_eevdf(cfs_rq) == task:
        resched = True
    return resched


def wakeup_preempt(cfs_rq, task):
    """
    Take this logic from core.c
    ttwu_do_active -> change state to running/ready, and enqueue_entity
    """

    task.state = TaskStatus.READY
    sched = enqueue_entity(cfs_rq, task)

    if cfs_rq.curr is None:
        return True  # No one is running — this task should run

    preempt = check_preempt_wakeup_fair(cfs_rq, task)
    if preempt:
        sched = True
    return sched
    # Lets just start with enqueueing first and making it work. And then we can try the check_preempt_wakeup_fair.
    #return check_preempt_wakeup_fair(cfs_rq, task)


def do_preempt_short(cfs_rq, pse, se):
    # Skip if the PREEMPT_SHORT feature is disabled.
    if not PREEMPT_SHORT:
        return False

    # Only consider preempting if the new task has a shorter slice than the current.
    if pse.slice >= se.slice:
        return False

    # The new task must be eligible to run.
    if not entity_eligible(cfs_rq, pse):
        return False

    # If the new task has an earlier virtual deadline, allow preemption.
    if entity_before(pse, se):
        return True

    # If the current task is not eligible, allow preemption.
    if not entity_eligible(cfs_rq, se):
        return True

    return False


# First some logic from core.c first.
# This is the only thing I need before calling check_prempt, which is wakeup_preempt
# def ttwu_do_activate(self, task):
#     task.state = "RUNNING"
#     self.enqueue_entity(task)
#     self.check_preempt(task)  # optional: only if modeling preemption

def cancel_protect_slice(se):
    if protect_slice(se):
        se.vlag = se.deadline + 1

def protect_slice(se):
    return se.vlag == se.deadline
