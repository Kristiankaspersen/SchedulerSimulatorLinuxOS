import greenlet
from schedsimulator.enums.process_status import TaskStatus
import random
class GreenletProc:
    def __init__(self, pid):
        self.pid = pid
        #self.greenlet = greenlet.greenlet(self.run)  # Create a greenlet for this process
        self.green = greenlet.greenlet(self.run)  # Pass self as an argument
        self.status = TaskStatus.NEW


        # ----- Unique props for this process ------
        self.cpu_work = random.randint(100, 1000000)
        self.cpu_work = 100
        self.other_number = self.cpu_work // 10
        self.other_number = 1000000

        # ----- necessary properties for old round-robin scheduler
        self.next = None  # Next process in round-robin scheduling
        self.prev = None  # Used in one implementation of round-robin scheduling
    #
    def run(self, scheduler):
        """Simulated CPU-bound task that gets preempted."""
        #print(f"▶️ Process {self.pid} started.")
        for i in range(self.cpu_work):  # Simulating CPU work
            if i % self.other_number == 0:
               #print(f"Process {self.pid} at step {i}")
                pass
            #greenlet.getcurrent().parent.switch()  # Voluntarily switch (will be overridden by SIGALRM)

        #print(f" Process {self.pid} finished execution.")

        scheduler.exit()