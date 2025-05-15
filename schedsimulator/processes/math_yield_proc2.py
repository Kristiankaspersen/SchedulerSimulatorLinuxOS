import time

import greenlet
from schedsimulator.enums.process_status import TaskStatus
from greenlet import getcurrent
from schedsimulator.enums.process_policy import Policy

class MathYieldProcess:
    def __init__(self, pid, priority, policy=Policy.SCHED_OTHER):
        self.pid = pid
        # self.greenlet = greenlet.greenlet(self.run)  # Create a greenlet for this process
        self.green = greenlet.greenlet(self.run)  # Pass self as an argument
        self.next = None  # Next process in round-robin scheduling
        self.prev = None
        self.status = TaskStatus.NEW
        self.counter = 0
        self.policy = policy
        self.priority = priority # Just set it to 50 for now.

    def run(self):
            """
            Generator that calculates sum of numbers recursively and yields execution.
            """
            DELAY_VAL = 0.1  # Simulation delay
            print(getcurrent().parent)


            def print_counter(done):
                    if done:
                        print(f"{self.pid} Exited")
                    else:
                        print(f"Process {self.pid} - {self.counter}")

            def rec(n):
                """Recursive sum function that yields execution at multiples of 37."""
                if n % 37 == 0:
                    self.status = TaskStatus.READY
                    self.green.parent.switch()
                if n == 0:
                    return 0
                else:
                    return n + rec(n - 1)

            # Main loop
            for i in range(101):

                result = rec(i)
                print(f"Did you know that 1 + ... + {i} = {result} - {self.pid}")

                print_counter(False)
                self.counter += 1
                self.status = TaskStatus.READY
                self.green.parent.switch()
                non_blocking_sleep(DELAY_VAL)  # Simulate delay

            print_counter(True)
            self.status = TaskStatus.READY
            self.green.parent.switch()  # Final yield before exiting
            self.status = TaskStatus.EXIT

def non_blocking_sleep(seconds):
    start_time = time.time()  # Get current time
    while time.time() - start_time < seconds:
        pass

