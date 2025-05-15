

from schedsimulator.old.linked_queue import TheQueue


class OSLock:
    def __init__(self, block_func, unblock_func, scheduler):
        self.blocked_queue = TheQueue()
        self.lock = False
        self.block_func = block_func
        self.unblock_func = unblock_func
        self.scheduler = scheduler

    def lock(self):
        if self.lock:
            self.scheduler.block(self.blocked_queue)
            # Pass in blocked queue
            # So do a block.
        else:
            self.lock = True

    def unlock(self):
        if self.blocked_queue.empty():
            self.lock = False
        else:
            self.scheduler.unblock(self.blocked_queue)






