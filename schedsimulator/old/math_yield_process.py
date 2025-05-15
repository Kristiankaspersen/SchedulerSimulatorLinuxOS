import time
from schedsimulator.enums.process_status import TaskStatus

class MathProcess:
    def __init__(self, pid):
        self.pid = pid
        self.status = TaskStatus.NEW
        self.counter = 0
        self.next = None
        self.prev = None
        self.gen = None # The generator object in the future.

    async def run(self, scheduler):
            """
            Generator that calculates sum of numbers recursively and yields execution.
            """
            DELAY_VAL = 0.1  # Simulation delay
            print("Does this even RUN??")

            def print_counter(done):
                    if done:
                        print(f"{self.pid} Exited")
                    else:
                        print(f"{self.pid} - {self.counter}")

            def rec(n):
                """Recursive sum function that yields execution at multiples of 37."""
                if n % 37 == 0:
                    scheduler.yields()
                    yield  # Yield execution to other processes
                if n == 0:
                    return 0
                else:
                    # Store the recursive result first
                    scheduler.yields()
                    recursive_result = yield from rec(n - 1)
                    return n + recursive_result  # Now we can safely return it

            # Main loop
            for i in range(101):
                scheduler.yields()
                #result = yield from rec(i)  # Yielding inside recursion
                #result = 0  # Initialize result
                #gen = rec(i)  # Create the normal generator manually
                result = 0
                gen = rec(i)
                try:
                    while True:
                        # Think I actually should yield here.
                        next(gen) #Resume execution until the next `yield`
                        yield #Preempt execution to simulate scheduling
                except StopIteration as e:
                    result += e.value
                print(f"Did you know that 1 + ... {i} = {result}")

                print_counter(False)
                self.counter += 1
                scheduler.yields()
                yield  # Yield execution to other processes
                time.sleep(DELAY_VAL)  # Simulate delay

            print_counter(True)
            #scheduler.yields()
            scheduler.exit()
            yield  # Final yield before exiting