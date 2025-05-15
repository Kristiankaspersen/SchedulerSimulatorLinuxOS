import greenlet
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.process_policy import Policy

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
BASE_SLICE2 = 12_000_000   # 12ms slice, in nanoseconds (Linux uses ns internally), something GPT found. 
BASE_SLICE = 2_250_000  #Found in kali systems
sched_latency_ns = 6_000_000 # 6ms slice
class Process:
    def __init__(self, pid, interactive, priority=50, nice=0, policy=Policy.SCHED_OTHER):
        self.pid = pid
        self.greenlet = greenlet.greenlet(self.run)  # Create a greenlet for this process
        self.policy = policy
        self.priority = priority  # Just start with the same priority
        # ------------ for CFS ------------------
        self.nice = nice
        self.weight = nice_to_weight[nice]
        self.vruntime = 0  # Total unscaled CPU time
        self.virtual_deadline = 0  # Will be updated
        self.current_end_time = 0 #
        self.current_start_time = 0


        #In update_curr in linux we do curr->sum_exac_runtime += delta_exac
        #
        self.sum_exac_runtime = 0 # This is the sum of all real times added together.

        ## ---------- not Ususal -----
        self.interactive = interactive # True or false

    def run(self):
        print("running")

    def update_virtual_deadline(self):
        # Calculate time slice (inversely proportional to weight)
        # The more weight, the shorter the virtual gap between runs
        period = BASE_SLICE * NICE_0_LOAD / self.weight

        # Deadline = now (vruntime) + when task should next run again
        self.virtual_deadline = self.vruntime + period

    def calc_delta_fair(self, delta):

        if self.weight != NICE_0_LOAD:
            #delta = __calc_delta(delta, NICE_0_LOAD, & se->load);
            delta = delta * (NICE_0_LOAD / self.weight)

        return delta
    def update_runtime(self):
        """Calculates current CPU time and adds to the total runtime for the process"""
        self.vruntime += self.current_end_time - self.current_start_time