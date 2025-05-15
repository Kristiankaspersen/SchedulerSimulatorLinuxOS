import time

from schedsimulator.enums.task_type import TaskType
from schedsimulator.globals import sysctl_sched_base_slice
#from schedsimulator.structures.task import Task
from schedsimulator.utils import calc_delta_fair, update_min_vruntime

from schedsimulator.globals import ADAPTIVE

import schedsimulator.globals as globs


def update_deadline(task):
    # (done)
    if (task.vruntime - task.deadline) < 0:
        return False

    # For EEVDF the virtual time slope is deterimned by w_I (iow. nice)
    # while the request time r_i is determined by sysctl_sched_base_slice
    if not task.custom_slice:
        task.slice = sysctl_sched_base_slice

    if ADAPTIVE:
        if task.type == TaskType.CPU:
            task.slice += globs.cpu_offset
        elif task.type == TaskType.RESP:
            task.slice += globs.interactive_offset

    # EEVDF: vd_i = ve_i + r_i / w_i
    # This just adds the slice, if the weight is 1024, and gets a
    task.deadline = task.vruntime + calc_delta_fair(task.slice, task)

    return True


def update_curr(cfs_rq):
    curr = cfs_rq.curr
    if curr is None:
        return False
    # Think is done
    #delta_exac = time.perf_counter_ns() - curr.exec_start
    delta_exac = update_curr_se(cfs_rq, cfs_rq.curr)
    #print(f"DELTA EXAC: {curr.exec_start}")
    #print(f"DELTA EXAC: {delta_exac}")

    # Done
    if delta_exac <= 0:
        #print("DOES THIS HAPPEN?!?!?!")
        return False

    curr.vruntime += calc_delta_fair(delta_exac, curr)
    resched = update_deadline(cfs_rq.curr)

    # Done
    update_min_vruntime(cfs_rq)
    return resched

#TODO update this as well.Write about this.
def update_curr_se(cfs_rq, curr):
    now = cfs_rq.virtual_global_clock_ns

    delta_exec = now - curr.exec_start
    if delta_exec <= 0: #Very unlikely
        return delta_exec
    curr.exec_start = now
    curr.sum_exec_runtime += delta_exec

    return delta_exec
