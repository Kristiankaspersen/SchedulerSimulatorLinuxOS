from schedsimulator.old.linked_queue import TheQueue


class OSSemaphore:
    def __init__(self,  init_counter):
        self.counter = max(0, init_counter)
        self.blocked_queue = TheQueue()
    def waitP(self, process, scheduler):
        # Teller 0 > eller høyere.
        if self.counter > 0:
            #Men du kommer inn i kritiks sone...
            self.counter -= 1
        elif self.counter == 0:
            #Du blir blokert.
            scheduler.block(self.blocked_queue)
            process.green.parent.switch()
        else:
            #Something is wrong, since it is negative.
            print("Something went wrong with the semaphore, because the value is negative")

    def signalV(self, process,  scheduler):
        if not self.blocked_queue.empty():
            scheduler.unblock(self.blocked_queue)
        else:
            self.counter += 1
            print("There is nothing to unblock, the blocked queue is empty")

