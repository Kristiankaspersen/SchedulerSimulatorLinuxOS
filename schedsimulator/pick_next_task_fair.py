import time

from schedsimulator.dequeue_task import __dequeue_entity
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.task_type import TaskType
from schedsimulator.globals import RUN_TO_PARITY
from schedsimulator.enqueue_task import __enqueue_entity
from schedsimulator.update_current import update_curr
from schedsimulator.utils import entity_eligible, protect_slice, entity_before, vruntime_eligible


def set_next_entity(cfs_rq, next):
    #if next.on_rq # You're checking on_rq, but earlier logic (like put_prev_entity) may have already called dequeue_entity(), which removed it from the tree but didn’t reset on_rq correctly
    if next.rb_node is not None:   # That guarantees you only remove it if it’s actually in the tree.
        __dequeue_entity(cfs_rq, next)
        #cfs_rq.task_timeline.print_tree()

    cfs_rq.curr = next
    cfs_rq.curr.on_rq = True

    # Do not know what I need with prev-sun_exc_runtime
    next.prev_sum_exec_runtime = next.sum_exec_runtime
    next.exec_start = cfs_rq.virtual_global_clock_ns  # Important for correct delta_exec!
    next.tick_offset = cfs_rq.virtual_global_clock_ns

    #Latency stats:
    calculate_latency(cfs_rq, next)


def calculate_latency(cfs_rq,  task):
    task.latency = time.time_ns() - task.enqueue_time
    task.latency_virtual = cfs_rq.virtual_global_clock_ns
    cfs_rq.latencies.append(task.latency)
    if task.type == TaskType.CPU:
        cfs_rq.cpu_latencies.append(task.latency)
        cfs_rq.cpu_latencies_virtual.append(task.latency_virtual)
    elif task.type == TaskType.RESP:
        cfs_rq.resp_latencies.append(task.latency)
        cfs_rq.resp_latencies_virtual.append(task.latency_virtual)

def put_prev_entity(cfs_rq, prev):
    if prev is not None:
        if prev.on_rq:
            update_curr(cfs_rq)

        if prev.on_rq:
        #if prev.rb_node is None:
            #print(f"enqueue pid: {prev.pid}")
            __enqueue_entity(cfs_rq, prev)   #simplified __enqueue_entity()

        assert cfs_rq.curr == prev, "BUG: prev task is not current!"
        cfs_rq.curr = None
    else:
        cfs_rq.curr = None


def pick_next_entity(cfs_rq):
    return pick_eevdf(cfs_rq)

def pick_task_fair(cfs_rq):
    # Might update_curr()
    return pick_next_entity(cfs_rq)

def pick_next_task_fair(cfs_rq, prev):
    # Ensure prev is gone if it's not runnable
    if prev and prev.status in [TaskStatus.EXIT, TaskStatus.BLOCKED]:
        if prev.rb_node is not None:
            print(f"It does not do this more then once {prev.pid} ")
            #assert False, "DOES THIS happen?? NEEEEVER"
            __dequeue_entity(cfs_rq, prev)  # Always call, since it's not removed yet
        prev = None

    #cfs_rq.task_timeline.print_tree()
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
        # __set_next_task_fair(rq, p, true);
    #print(f"\nNext task pid: {next.pid}, deadline: {next.deadline}, min_vruntime {next.min_vruntime}\n")
    #cfs_rq.task_timeline.print_tree()
    set_next_entity(cfs_rq, next)
    return next

def pick_eevdf(cfs_rq):
    # TODO need to check if pick_first_entity is correct.
    node = cfs_rq.task_timeline.root
    task = cfs_rq.task_timeline.pick_first_entity()
    curr = cfs_rq.curr
    best = None

    #cfs_rq.task_timeline.print_tree()

    # I added this, since if not we get an error of node.min_vruntime not existing.
    if node is None:
        if curr and curr.on_rq:
            return curr
        return None

    if cfs_rq.nr_queued == 1:
        return curr if curr and curr.on_rq else task

    #TODO not needed, I included this
    if not vruntime_eligible(cfs_rq, node.min_vruntime):
        #assert False,  "Should not happen.."
        return curr  # no entity is eligible yet

    if curr and (not curr.on_rq or not entity_eligible(cfs_rq, curr)):
        curr = None

    if RUN_TO_PARITY and curr and protect_slice(curr):
        return curr

    # Find the leftmost (earliest deadline) eligible entity
    if task and entity_eligible(cfs_rq, task):
        best = task
    else:
        # best = find_eligible_entity(node, cfs_rq)
        #Heap search for the EEVD entity
        while node is not None:
            left = node.left
            # Eligible entities in left subtree are always better
            # choice, since they have earlier deadline.
            if left and vruntime_eligible(cfs_rq, left.min_vruntime):
                node = left
                continue
            task = node.task

            if entity_eligible(cfs_rq, task):
                best = task
                break
            node = node.right

    #found
    if (best is None) or ((curr is not None) and entity_before(curr, best)):
        best = curr

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