from schedsimulator.structures.linked_queue import TheQueue


class OSLock:
    """Simple cooperative lock for generator-based scheduling."""
    def __init__(self):
        self.locked = False  # Indicates if the lock is taken
        self.blocked_queue = TheQueue() # Queue for waiting generators

    def acquire(self, process, scheduler):
        """Attempt to acquire the lock, otherwise queue the process."""
        if self.locked:
            #self.waiting_queue.append(process)  # Process waits
            scheduler.block(self.blocked_queue)
            #Må gjøre en yield nå. Da er det viktig at status er blocked, for vi skal ikke skifte på noe nå, siden vi gjorde det når vi blokkerte.
            process.green.parent.switch()
        else:
            self.locked = True
            #process.status = PCBStatus.READY (ikke vits egentlig)
            # Her går vi inn til critical section.

    def release(self, scheduler):
        """Release the lock and wake up the next waiting process if any."""
        if not self.blocked_queue.empty():
            scheduler.unblock(self.blocked_queue)
        else:
            self.locked = False  # No one is waiting, release the lock