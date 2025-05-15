from schedsimulator.update_current import update_curr


# This is going to be the TICKER in the scheduler


def entity_tick(cfs_rq):
    """
    - This return True, if need resched, and False otherwise.
    - Also it forwards the vruntime..
    """
    return update_curr(cfs_rq)

def task_tick_fair(cfs_rq):
    return entity_tick(cfs_rq)