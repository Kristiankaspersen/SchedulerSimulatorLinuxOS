import greenlet
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.process_policy import Policy
import random

from schedsimulator.enums.task_type import TaskType

NICE_0_LOAD = 1024  # baseline weight for nice=0

nice_to_weight = {
    -20: 88761, -19: 71755, -18: 56483, -17: 46273, -16: 36291,
    -15: 29154, -14: 23254, -13: 18705, -12: 14949, -11: 11916,
    -10: 9548, -9: 7620, -8: 6100, -7: 4904, -6: 3906,
    -5: 3121, -4: 2501, -3: 1991, -2: 1586, -1: 1277,
    0: 1024, 1: 820, 2: 655, 3: 526, 4: 423,
    5: 335, 6: 272, 7: 215, 8: 172, 9: 137,
    10: 110, 11: 87, 12: 70, 13: 56, 14: 45,
    15: 36, 16: 29, 17: 23, 18: 18, 19: 15
}
BASE_SLICE = 12_000_000   # 12ms slice, in nanoseconds (Linux uses ns internally)

class CPUHeavyProc:
    def __init__(self, type, pid, priority=50, nice=0, policy=Policy.SCHED_OTHER):
        self.pid = pid
        # self.greenlet = greenlet.greenlet(self.run)  # Create a greenlet for this process
        self.green = greenlet.greenlet(self.run)  # Pass self as an argument
        self.status = TaskStatus.NEW
        self.policy = policy
        self.priority = 50  # Just start with the same priority
        # ------------ for CFS ------------------
        self.nice = nice
        self.weight = nice_to_weight[nice]
        self.vruntime = 0  # Total unscaled CPU time. So its not virtual, its actually runtime.
        self.virtual_deadline = 0  # Will be updated
        self.current_start_time = 0
        self.current_end_time = 0
        self.current_cpu_time = 0 # This is the same as delta_exec_ns, use this to update vruntime.

        # ----- Unique props for this process ------
        self.cpu_work = random.randint(100, 1000000)
        self.cpu_work = 1000
        self.other_number = self.cpu_work // 10
        self.other_number = 1000000
        self.tick_count = 0
        self.type = type

        # ----- necessary properties for old round-robin scheduler
        self.next = None  # Next process in round-robin scheduling
        self.prev = None  # Used in one implementation of round-robin scheduling

    def run(self):
        """Simulated CPU-bound task that gets preempted."""
        # print(f"▶️ Process {self.pid} started.")

        if self.type == TaskType.CPU:
            print(f"CPU: {self.pid}")
            compute = 0
            while self.tick_count <= 10:
                compute += 1

            print(self.tick_count)
            self.status = TaskStatus.EXIT
            greenlet.getcurrent().parent.switch()
        elif self.type == TaskType.RESP:
            print(f"RESP: {self.pid}")
            compute = 0
            while self.tick_count <= 400:
                compute += 1

                if self.tick_count % 3 == 0:
                    self.status = TaskStatus.BLOCKED
                    greenlet.getcurrent().parent.switch()

            print(self.tick_count)
            self.status = TaskStatus.EXIT
            greenlet.getcurrent().parent.switch()
        else:
            print(f"IO: {self.pid}")
            compute = 0
            while self.tick_count <= 20:
                compute += 1

                if self.tick_count % 10 == 0:
                    self.status = TaskStatus.BLOCKED
                    greenlet.getcurrent().parent.switch()

            print(self.tick_count)
            self.status = TaskStatus.EXIT
            greenlet.getcurrent().parent.switch()




    # def run(self):
    #     """Simulated CPU-bound task that gets preempted."""
    #     # print(f"▶️ Process {self.pid} started.")
    #     for i in range(self.cpu_work):  # Simulating CPU work
    #         if i == 10000:
    #             print(f"Doing work {self.pid}" )
    #         if i == 1000:
    #              self.status = TaskStatus.BLOCKED
    #              greenlet.getcurrent().parent.switch()
    #
    #
    #         if i % self.other_number == 0:
    #             # print(f"Process {self.pid} at step {i}")
    #             pass
    #         # greenlet.getcurrent().parent.switch()  # Voluntarily switch (will be overridden by SIGALRM)
    #
    #     # print(f" Process {self.pid} finished execution.")
    #
    #     self.status = TaskStatus.EXIT
    #     greenlet.getcurrent().parent.switch()

    def update_virtual_deadline(self):
        """Updates the virtual deadline"""
        # Calculate time slice (inversely proportional to weight)
        # The more weight, the shorter the virtual gap between runs
        period = BASE_SLICE * NICE_0_LOAD / self.weight

        # Deadline = now (vruntime) + when task should next run again
        self.virtual_deadline = self.vruntime + period

    def update_runtime(self):
        """Calculates current CPU time and adds to the total runtime for the process"""
        self.vruntime += self.current_end_time - self.current_start_time