from schedsimulator.enums.task_type import TaskType
from schedsimulator.globals import TICK_NSEC
from schedsimulator.utils import avg_vruntime, calc_delta_fair, avg_vruntime_sub, update_min_vruntime
from schedsimulator.update_current import update_curr


def update_entity_lag(cfs_rq, task):
    """
    (This implementation is done)
    Called when a task is dequeued.
    - It calculates the task’s virtual lag relative to the system virtual time (avg_vruntime(cfs_rq) - task.vruntime)
    - To prevent excessive lag swings due to task insertion and removal, the computed lag is clamped within a bounded range between −limit and +limit
    """
    vlag = avg_vruntime(cfs_rq) - task.vruntime
    limit = calc_delta_fair(max(2 * task.slice, TICK_NSEC), task)
    task.vlag = max(-limit, min(vlag, limit))  # clamp to [-limit, limit]


# Missing
def __dequeue_entity(cfs_rq, task):
    cfs_rq.task_timeline.remove(task)
    task.on_rq = False
    task.rb_node = None
    avg_vruntime_sub(cfs_rq, task)
    sub_task_type(cfs_rq, task)


def sub_task_type(cfs_rq, task):
    if task.type == TaskType.CPU:
        cfs_rq.num_cpu -= 1
    elif task.type == TaskType.RESP:
        cfs_rq.num_interactive -= 1
    else:
        cfs_rq.num_other -= 1

#TODO: Think about resched and stuff like that, in dequeue, how do I handle that
#DAMN, then I really need to return resched.
def dequeue_entity(cfs_rq, task):
    update_curr(cfs_rq)
    update_entity_lag(cfs_rq, task)

    # Need to update how many tasks there are of the types:
    if task.type == TaskType.RESP:
        cfs_rq.num_interactive -= 1
    elif task.type == TaskType.CPU:
        cfs_rq.num_cpu -= 1
    else:
        cfs_rq.num_other -= 1
    """
    the task!= cfs_rq.curr is not straight forward
    - seems like when something !preempt (meaning, block/sleep or exit) -> look at try_block in __schedule( in core. 
    - Then it will eventually call dequeue, but when calling dequeue, its still current running, meaning it will not get removed
    - from the rbtree, but only marked as rq->on_rq = 0. 
    - (not sure where it eventuelly gets removed)
    - Later though -> #define RCU_INIT_POINTER(p, v) -> this parts does this rq->curr = next. 
    - Block ->
        Effect:
            Because on_rq = 0, the task will no longer be considered in the runqueue,
            even though its rb-tree node stays in place.

            When the task wakes up (wake_up()),
            it re-inserts itself into the rbtree via enqueue_entity().

            So:
            → yes, logically removed, but physical removal is avoided in hotpath
            to avoid corruption or unnecessary tree rebalance while curr is live.
    - Exit -> 
    -    do_exit() → sets task state to EXIT_ZOMBIE
    -    Cleanup happens outside the scheduler
         (e.g., release_task(), free_task()),
          and the task is effectively gone.
          → yes, logically removed, cleaned up later — no need to hit __dequeue_entity() during switch.
    - Why avoid __dequeue_entity() on curr?
        Because:
            - The task is still technically running → you don’t want to modify the tree while it’s live.
            - Setting on_rq = 0 is enough to “hide” it from the scheduler.
            - It keeps the switching path fast and avoids unnecessary rbtree churn.
    - 
    """
    """
    - The reason its not needed to dequeue if its current, its because its not in the red-black treee
    -   (when we block, sleep, exit etc. Before doing pick_next) 
    - but its on_rq = 1, since its in a way in the queue, but then we set this to 0. 
    - The dequeing happens when we pick the next
    """
    if task != cfs_rq.curr and task.on_rq:
        print(f"In Dequeue, doing __dequuee, does it happen here? {task.pid}")
        __dequeue_entity(cfs_rq, task) # This is the only thing I am missing now for my code.

    cfs_rq.task_timeline.print_tree()
    assert task.on_rq, f"BUG: Trying to dequeue task not on runqueue (pid={task.pid})"
    task.on_rq = False
    cfs_rq.nr_queued -= 1 # Not in real code
    assert cfs_rq.nr_queued >= 0, f"BUG: nr_queued went negative at PID={task.pid}"

    # Maybe I am missing some shit here..
    update_min_vruntime(cfs_rq)





# This is the top of the func:
def enqueue_task(cfs_rq, task):
    dequeue_entity(cfs_rq, task)