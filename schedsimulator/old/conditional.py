from schedsimulator.old.linked_queue import TheQueue


class ConditionalVariable:
    def __init__(self, scheduler):
        self.blocked_queue = TheQueue()
        self.scheduler = scheduler

    def wait(self, condition):
        while not condition:
            # put in blocked queue.
            self.scheduler.block(self.blocked_queue)

    def notify(self):
        # Think the first in the queue will be released.
        self.scheduler.unblock(self.blocked_queue)

    def notify_all(self):
        # All from th queue will be released.
        while not self.blocked_queue.empty():
            self.scheduler.unblock(self.blocked_queue)
