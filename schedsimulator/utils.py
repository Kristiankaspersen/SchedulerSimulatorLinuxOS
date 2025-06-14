import time

from schedsimulator.globals import NICE_0_LOAD, sysctl_sched_base_slice




# Not needed, since we never scale up...
SCHED_FIXEDPOINT_SHIFT = 10
def scale_load_down(w):
    if w:
        w = max(2, w >> SCHED_FIXEDPOINT_SHIFT)
    return w

def avg_vruntime_add(cfs_rq, task):
    weight = task.weight #Think if scaling is needed.
    cfs_rq.avg_vruntime += entity_key(cfs_rq, task) * weight
    cfs_rq.avg_load += weight

def avg_vruntime_sub(cfs_rq, task):
    weight = task.weight #Think if scaling is needed.
    cfs_rq.avg_vruntime -= entity_key(cfs_rq, task) * weight
    cfs_rq.avg_load -= weight

def calc_delta_fair(delta_exac, task):
    # When I use NICE_0_LOAD, this just becomes 1 * delta_exac
    return delta_exac * (NICE_0_LOAD // task.weight)

def entity_key(cfs_rq, task):
    return task.vruntime - cfs_rq.min_vruntime

def avg_vruntime(cfs_rq):
    """
    This is used in:
    - place_entity() (enqueue) (vruntime = avg_vruntime())
    - update_entity_lag() (dequeue) (vlag = avg_vruntime() - task.vruntime)
    """
    curr = cfs_rq.curr
    avg = cfs_rq.avg_vruntime
    load = cfs_rq.avg_load

    if curr and curr.on_rq:
        weight = curr.weight #In Linux this is scaled, not needed here.
        avg += entity_key(cfs_rq, curr) * weight
        load += weight

    #This is where the bias happens.
    if load > 0:
        if avg < 0:
            avg -= (load - 1)
        avg = avg // load

    # Add offset to min_vruntime to get avg_vruntime
    return cfs_rq.min_vruntime + avg

def avg_vruntime_update(cfs_rq, delta):
    #v' = v + d ==> avg_vruntime' = avg_runtime - d * avg_load
    cfs_rq.avg_vruntime -= cfs_rq.avg_load * delta

def __update_min_vruntime(cfs_rq, vruntime):
    min_vruntime = cfs_rq.min_vruntime
    delta = vruntime - min_vruntime

    if delta > 0:
        avg_vruntime_update(cfs_rq, delta)
        min_vruntime = vruntime
    return min_vruntime


def update_min_vruntime(cfs_rq):
    root_node = pick_root_entity(cfs_rq) #task = pick_root_entity(cfs_run_queue)
    curr = cfs_rq.curr
    vruntime = cfs_rq.min_vruntime

    if curr:
        if curr.on_rq:
            vruntime = curr.vruntime
        else:
            curr = None

    if root_node:
        if not curr:
            vruntime = root_node.min_vruntime
        else:
            vruntime = min(vruntime, root_node.min_vruntime)

    # Ensure we never gain time by being placed backwards.
    cfs_rq.min_vruntime = __update_min_vruntime(cfs_rq, vruntime)


# Eligible part

def vruntime_eligible(cfs_rq, vruntime):
    # Think is done.
    curr = cfs_rq.curr
    avg = cfs_rq.avg_vruntime
    load = cfs_rq.avg_load

    if curr and curr.on_rq:
        weight = curr.weight
        avg += entity_key(cfs_rq, curr) * weight
        load += weight
    return avg >= (vruntime - cfs_rq.min_vruntime) * load

def entity_eligible(cfs_rq, task):
    return vruntime_eligible(cfs_rq, task.vruntime)


def entity_before(entity1, entity2):
    # Return True if entity1 has earlier deadline than entity2
    #return entity1.deadline < entity2.deadline
    return entity1.deadline - entity2.deadline < 0

# Think about this one...
def protect_slice(task):
    # Placeholder for slice protection logic
    return task.vlag == task.deadline

def pick_root_entity(cfs_rq):
    """
    Picks the root sched_entity from the CFS runqueue's red-black tree.

    Args:
        cfs_rq: An instance of CFSRunqueue, which has a 'tasks_timeline' attribute.

    Returns:
        The sched_entity at the root of the tree, or None if the tree is empty.
    """
    root = cfs_rq.task_timeline.root  # assuming you name it 'root' in Python

    if root is None:
        return None

    return root.task