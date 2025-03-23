import curses
import time
import greenlet
from schedsimulator.structures.process_status import PCBStatus


class MathYieldProcess:
    def __init__(self, pid):
        self.pid = pid
        # self.greenlet = greenlet.greenlet(self.run)  # Create a greenlet for this process
        self.green = greenlet.greenlet(self.run)  # Pass self as an argument
        self.next = None  # Next process in round-robin scheduling
        self.prev = None
        self.status = PCBStatus.NEW
        self.counter = 0

    def run(self, scheduler):
            """
            Generator that calculates sum of numbers recursively and yields execution.
            """
            DELAY_VAL = 0.1  # Simulation delay


            def print_counter(done):
                    if done:
                        print(f"{self.pid} Exited")
                    else:
                        print(f"Process {self.pid} - {self.counter}")

            def rec(n):
                """Recursive sum function that yields execution at multiples of 37."""
                if n % 37 == 0:
                    scheduler.yields()
                    self.green.parent.switch()
                if n == 0:
                    return 0
                else:
                    return n + rec(n - 1)

            # Main loop
            for i in range(101):

                result = rec(i)
                print(f"Did you know that 1 + ... + {i} = {result}")

                print_counter(False)
                self.counter += 1
                scheduler.yields()
                self.green.parent.switch()
                scheduler.non_blocking_sleep(DELAY_VAL)  # Simulate delay

            print_counter(True)
            scheduler.yields()
            self.green.parent.switch()  # Final yield before exiting
            scheduler.exit()
