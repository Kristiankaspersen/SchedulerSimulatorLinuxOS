import time

from schedsimulator.dequeue_task import __dequeue_entity
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.task_type import TaskType
from schedsimulator.globals import RUN_TO_PARITY
from schedsimulator.enqueue_task import __enqueue_entity
from schedsimulator.update_current import update_curr
from schedsimulator.utils import entity_eligible, protect_slice, entity_before, vruntime_eligible


def set_next_entity(cfs_rq, next):
    if next.rb_node is not None:   # That guarantees you only remove it if it’s actually in the tree.
        __dequeue_entity(cfs_rq, next)

    cfs_rq.curr = next
    cfs_rq.curr.on_rq = True

    next.prev_sum_exec_runtime = next.sum_exec_runtime
    next.exec_start = cfs_rq.virtual_global_clock_ns  # Important for correct delta_exec!
    next.tick_offset = cfs_rq.virtual_global_clock_ns

    #Latency stats:
    calculate_latency(cfs_rq, next)


def calculate_latency(cfs_rq,  task):
    task.latency = time.time_ns() - task.enqueue_time
    task.latency_virtual = task.exec_start - task.enqueue_time_virtual
    cfs_rq.latencies.append(task.latency)
    if task.type == TaskType.CPU:
        cfs_rq.cpu_latencies.append(task.latency)
        cfs_rq.cpu_latencies_virtual.append(task.latency_virtual)
    elif task.type == TaskType.RESP:
        cfs_rq.resp_latencies.append(task.latency)
        cfs_rq.resp_latencies_virtual.append(task.latency_virtual)
    else:
        cfs_rq.io_latencies.append(task.latency)


def put_prev_entity(cfs_rq, prev):
    if prev is not None:
        if prev.on_rq:
            update_curr(cfs_rq)

        if prev.on_rq:
            __enqueue_entity(cfs_rq, prev)

        assert cfs_rq.curr == prev, "BUG: prev task is not current!"
        cfs_rq.curr = None
    else:
        cfs_rq.curr = None


def pick_next_entity(cfs_rq):
    return pick_eevdf(cfs_rq)

def pick_task_fair(cfs_rq):
    return pick_next_entity(cfs_rq)

def pick_next_task_fair(cfs_rq, prev):
    # Ensure prev is gone if it's not runnable
    if prev and prev.status in [TaskStatus.EXIT, TaskStatus.BLOCKED]:
        if prev.rb_node is not None:
            __dequeue_entity(cfs_rq, prev)
        prev = None
        cfs_rq.curr = None

    next = pick_task_fair(cfs_rq)

    if not next:
        # Nothing else to run, continue with prev if it's valid
        if prev is not None:
            cfs_rq.curr = prev
        else:
            cfs_rq.curr = None


        return prev

    if next != prev:
        put_prev_entity(cfs_rq, prev)

    set_next_entity(cfs_rq, next)
    return next

def pick_eevdf(cfs_rq):
    node = cfs_rq.task_timeline.root
    task = cfs_rq.task_timeline.pick_first_entity()
    curr = cfs_rq.curr
    best = None

    # I added this, since if not we get an error of node.min_vruntime not existing.
    if node is None:
        if curr and curr.on_rq:
            return curr
        return None

    if cfs_rq.nr_queued == 1:
        return curr if curr and curr.on_rq else task

    if curr and (not curr.on_rq or not entity_eligible(cfs_rq, curr)):
        curr = None

    if RUN_TO_PARITY and curr and protect_slice(curr):
        return curr

    # Find the leftmost (earliest deadline) eligible entity
    if task and entity_eligible(cfs_rq, task):
        best = task
    else:
        # Found a potantial bug in the code I mirrored from linux, therefore I used this function instead.
        # This function makes sure it finds something eligible.

        best = find_eligible_entity(node, cfs_rq)
        # Potential bugs:
        # - Checks left without ever checking root, and the right from root.
        # - Also when we go right again, we go to the left at once, again without checking the right node.
        # #Heap search for the EEVDF entity
        # while node is not None:
        #     left = node.left
        #     # Eligible entities in left subtree are always better
        #     # choice, since they have earlier deadline.
        #     if left and vruntime_eligible(cfs_rq, left.min_vruntime):
        #         node = left
        #         continue
        #     task = node.task
        #
        #     if entity_eligible(cfs_rq, task):
        #         best = task
        #         break
        #     node = node.right

    #found
    if (best is None) or ((curr is not None) and entity_before(curr, best)):
        best = curr

    assert not (cfs_rq.task_timeline.root is not None and best is None), \
        "BUG: task_timeline has a root, but no best task was selected"

    return best


def find_eligible_entity(node, cfs_rq):
    if node is None:
        return None

    # First check left subtree
    left_best = find_eligible_entity(node.left, cfs_rq)
    if left_best:
        return left_best  # always prefer leftmost eligible

    # Then check this node
    if entity_eligible(cfs_rq, node.task):
        return node.task
    # Then check right subtree
    return find_eligible_entity(node.right, cfs_rq)