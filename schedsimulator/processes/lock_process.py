import curses
import time

import greenlet

from schedsimulator.structures.linked_queue import TheQueue
from schedsimulator.structures.process_status import PCBStatus
from schedsimulator.structures.locks import OSLock
from schedsimulator.structures.semaphore import OSSemaphore




class LockProcess:
    """Simulates two threads working on a shared value."""
    lock = OSLock()
    sem = OSSemaphore(1)
    shared_value = 0
    shared_exit_count = 0

    def __init__(self, pid, yield_freq):
        self.pid = pid
        self.counter = 0
        self.status = PCBStatus.NEW
        self.next = None
        self.prev = None
        self.green = greenlet.greenlet(self.run)
        self.yield_freq = yield_freq  # Determines how often it yields inside the critical section

    def run(self, scheduler):
        """Generator function simulating lock usage."""
        DELAY_VAL = 0.05  # Simulated delay

        i = 0
        while i < 100:
            #LockProcess.lock.acquire(self, scheduler)
            LockProcess.sem.waitP(self, scheduler)
            # Critical section (protected by lock)
            tmp = LockProcess.shared_value
             # Increment shared variable
            if i % self.yield_freq == 0:  # Simulate yield inside critical section
                scheduler.yields()
                self.green.parent.switch()

            LockProcess.shared_value = tmp + 1
            #LockProcess.lock.release(scheduler)  # Release lock
            LockProcess.sem.signalV(self, scheduler)
            print(f"Thread {self.pid} (lock)      : {LockProcess.shared_value}")

            i += 1
            scheduler.non_blocking_sleep(DELAY_VAL)
            scheduler.yields()
            self.green.parent.switch() # Yield execution to others

        LockProcess.shared_exit_count += 1  # Track exit count
        print(f"Thread {self.pid} (lock)      : {LockProcess.shared_value}")
        if LockProcess.shared_exit_count == 2:
            print("Passed" if LockProcess.shared_value == 200 else "Failed")
        else:
            print("Passed" if LockProcess.shared_value == 200 else "Failed")
        self.green.parent.switch()

        scheduler.non_blocking_sleep(DELAY_VAL) # Ensure output is visible before exiting
        scheduler.exit()









