from schedsimulator.structures.red_black_tree import RedBlackTree
from collections import deque

class CfsRunQueue:
    def __init__(self):
        self.task_timeline = RedBlackTree()
        # Do without timeline now first.
        self.curr = None
        self.avg_vruntime = 0 # sum(vruntime - min_vruntime) * weight (do not need to use scaled weight)
        self.avg_load = 0 # Named: tot_load_weight (consider renaming) avg_load in linx -> Tot weight accross tasks. (do not need to use scaled weight)
        self.min_vruntime = 0 # Smallest vruntime in the tree
        self.nr_queued = 0 # All nodes in the tree.
        self.virtual_global_clock_ns = 0
        self.latencies = []
        self.resp_latencies = []
        self.resp_latencies_virtual = deque(maxlen=50)
        self.cpu_preempt_intervals = deque(maxlen=50)
        self.cpu_latencies = []
        self.cpu_latencies_virtual = []
        self.num_interactive = 0
        self.num_cpu = 0
        self.num_other = 0