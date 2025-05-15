import time

from schedsimulator.enums.task_type import TaskType
from schedsimulator.globals import sysctl_sched_base_slice, PLACE_LAG, INIT_TREE, TICK_NSEC
#from schedsimulator.structures.task import Task
from schedsimulator.utils import avg_vruntime, calc_delta_fair, avg_vruntime_add
from schedsimulator.update_current import update_curr
import schedsimulator.globals as globals

initial_deadline_diff = 0
initial_vr_diff = 0


def enqueue_entity(cfs_rq, task):

    """
    - If the entity is current, we need to renormalize its position (since it’s about to go back into the runqueue).
    - -> Therefore place_entity, before update_curr.
    - We call place_entity() early before update_curr() to account for the fact that update_curr() may change time accounting.
    - For non-current entities:
    - -> We call place_entity() after the load updates (update_curr()), because we first want to update the runqueue clock, then figure out where to place the entity.

    -----------------
    When is the current running task doing enqueue_entity()?
    -This happens when: The current task is going back onto the runqueue.
    Examples:
        Preemption / time slice expiration:
        The current task runs out of time, and the scheduler picks a new task.
        → We enqueue the current task back into the red-black tree.
        - Voluntary yield (sched_yield()): The task gives up the CPU and goes back into the runqueue.
        - Explicit requeue during scheduling:
        For example, task wakes up but remains on the same CPU and will be requeued.
        BUT!
        In the Linux scheduler, the current task is not in the rb-tree while running.
        that’s why we need to renormalize it first (place_entity()), but we don’t call __enqueue_entity() until it’s truly back in the runqueue.
        For your Python simulation
       You can mimic this logic:
       - For non-current tasks, put them into your scheduling queue.
       - For current task, just prepare its accounting — you don’t insert it into the queue until it’s off CPU.
    """
    curr = cfs_rq.curr == task

    # Need to update how many tasks there are of the types:
    if task.type == TaskType.RESP:
        cfs_rq.num_interactive += 1
    elif task.type == TaskType.CPU:
        cfs_rq.num_cpu += 1
    else:
        cfs_rq.num_other += 1

    if curr:
        print("IS curr the one being enqueued?")
        place_entity(cfs_rq, task)

    resched = update_curr(cfs_rq)

    if not curr:
        place_entity(cfs_rq, task)

    if INIT_TREE:
        globals.initial_vr_diff += TICK_NSEC
        task.vruntime = globals.initial_vr_diff
        #initial_vr_diff += TICK_NSEC
        #globals.initial_deadline_diff += 1
        vslice = calc_delta_fair(task.slice, task)
        task.deadline = task.vruntime + vslice

    # account_entity_enqueue() TODO: Add this later
    cfs_rq.nr_queued += 1 # Only do this for now. Its done in account_entity_enqueue()
    assert cfs_rq.nr_queued >= 0, f"BUG: nr_queued went negative at PID={task.pid}"

    # update_stats_enqueue_fair() TODO: perhaphs necessary for RL
    if not curr:
        assert task is not cfs_rq.curr, f"BUG: tried to enqueue curr (pid={task.pid}) into tree"
        __enqueue_entity(cfs_rq, task)

    task.on_rq = True
    assert task.on_rq, "dsadnkjadnka"
    print(task.pid)

    return resched


def place_entity(cfs_rq, task):

    if not task.custom_slice:
        task.slice = sysctl_sched_base_slice

    if globals.ADAPTIVE:
        if task.type == TaskType.CPU:
            task.slice += globals.cpu_offset
        elif task.type == TaskType.RESP:
            task.slice += globals.interactive_offset

    vruntime = avg_vruntime(cfs_rq)
    vslice = calc_delta_fair(task.slice, task)
    lag = 0
    # TODO: Implement a lag version as well, here, where I try one with or without the lag implementation.
    if PLACE_LAG and cfs_rq.nr_queued > 0 and task.vlag != 0:
        """
        Make sure lag correction only applies when: 
        - The feature is enabled
        - There are other tasks on the runqueue
        - The task actually had a meaningful vlag before
        
        avg_load -> represents the total weight of all enqueued tasks. In linux its used to calculate the new average virtual time.
        
        Correct_vlag = (W + w_i) * vlag / W 
        - Why: This compensates for how the added task will shift the runqueue's average virtual time
        - Failing to do this will make tasks lose their relative "position in time" over time. 
        """
        # # This is the stored virtual lag from when the task was last dequeued
        lag = task.vlag
        # Get current runqueue load (sum of weights of all tasks)
        load = cfs_rq.avg_load # avg_load This should be the sum of scaled weights from runqueue
        if cfs_rq.curr and cfs_rq.curr.on_rq:
            load += cfs_rq.curr.weight # Must match scaling with average load

        # To prevent division by zero
        if load == 0:
            load = 1


        # Apply lag inflation to preserve the original lag after placement
        corrected_lag = ((load + task.weight) * lag)/ load
        lag = corrected_lag


    # Place the task into the timeline (shift back by lag if needed)
    task.vruntime = vruntime - lag

    # Set the initial deadline using EEVDF: vd_i = ve_i + r_i / w_i
    task.deadline = vruntime + vslice


def __enqueue_entity(cfs_rq, task):
    #TODO aslo need to insert the min_vruntime part
    # Think we are good here, with the min_vruntime..
    task.enqueue_time = time.time_ns()
    task.enqueue_time_virtual = cfs_rq.virtual_global_clock_ns
    avg_vruntime_add(cfs_rq, task)
    cfs_rq.task_timeline.insert(task)
    add_task_type(cfs_rq, task)


def add_task_type(cfs_rq, task):
    if task.type == TaskType.CPU:
        cfs_rq.num_cpu += 1
    elif task.type == TaskType.RESP:
        cfs_rq.num_interactive += 1
    else:
        cfs_rq.num_other += 1













def enqueue_task_fair(task):
    enqueue_entity(task)


