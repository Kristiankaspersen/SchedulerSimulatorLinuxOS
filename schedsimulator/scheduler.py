import signal
import time
import greenlet

from schedsimulator.Exceptions.greenletDeadExc import GreenletDeadError
from schedsimulator.processes.cpu_heavy_proc import GreenletProc
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.process_policy import Policy
from schedsimulator.processes.cpu_heavy_proc2 import CPUHeavyProc
from schedsimulator.processes.math_yield_proc2 import MathYieldProcess
from schedsimulator.structures.red_black_tree import RedBlackTree


# Test this as round robin scheduler....

class RTScheduler:
    MAX_RT_PRIORITIES = 100
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
    def __init__(self):
        self.deadline_queue = []
        self.idle_queue = []
        #self.red_black_tree = RedBlackTree()
        # Think about adjusting to linked list.
        self.priority_queue = [[] for _ in range(self.MAX_RT_PRIORITIES)]
        self.bitmap = 0
        self.current_running_proc = None

        signal.signal(signal.SIGALRM, self.preempt_handler)
        signal.setitimer(signal.ITIMER_REAL, 0.1, 0.1)  # 100ms time slice

    def preempt_handler(self, signum, frame):
        """Handles preemption by switching back to the scheduler."""
       # print(f"SIGALRM received! Preempting process {self.current_process.pid}")
        self.current_running_proc.status = TaskStatus.READY
        # Explicitly switch back to the scheduler
        self.current_running_proc.green.parent.switch()

    def set_bit(self, prio): self.bitmap |= (1 << prio)

    def clear_bit(self, prio): self.bitmap &= ~(1 << prio)

    def is_set(self, prio): return (self.bitmap & (1 << prio)) != 0

    def find_first_set(self):
        """This will find the highest priority and return"""
        for prio in range(100):
            if self.bitmap & (1 << prio):
                return prio
        return None

    def is_bitmap_empty(self):
        return self.bitmap == 0

    def add_proc_ready_queue(self, process):
        # Based on policy we do different adds.
        if Policy.is_deadline(process.policy):
            pass   # Potentially implement later.
        elif Policy.is_realtime(process.policy):
            # Add to FIFO Ready queues
            process.status = TaskStatus.READY
            self.priority_queue[process.priority].append(process)
            self.set_bit(process.priority)
        elif Policy.is_cfs(process.policy):
            # Add to Red-black ready queue

            if process.policy == Policy.SCHED_BATCH:
                pass
            else:
                # If SCHED_OTHER / SCHED_NORMAL
                # Add
                # Need to do some changes here, and also find out what I neeed to do to calculate the new values etc.
                # Calc time
                self.current_running_proc.start_time = time.perf_counter_ns()
                self.red_black_tree.insert(self.current_running_proc)
                pass
        else:
            if process.policy == Policy.SCHED_IDLE:
                pass
            print("Wrong policy")

    def queue_next_proc(self):
        prio = self.find_first_set()
        current_proc = None
        if prio is not None:
            if self.priority_queue[prio]:
                print(f"prio - {prio}")
                current_proc = self.priority_queue[prio].pop(0)
                if not self.priority_queue[prio]:
                    self.clear_bit(prio)
                print(current_proc.pid)
            else:
                self.clear_bit(prio)
                print("Nothing to remove in ready queue with this priority")
        else:
            print("the RT queue is empty")

        return current_proc

    def queue_next_proc_RBT(self):
        return self.red_black_tree.get_next_process()

    def schedule_next_process(self):
        # Before this I need a function that puts current running in the correct ready queue.
        # Put current running
        while True:
            if  self.current_running_proc.status == TaskStatus.NEW:
                print("ADDING PROC")
                self.add_proc_ready_queue(self.current_running_proc)
            elif self.current_running_proc.status == TaskStatus.READY:
                self.current_running_proc.end_time = time.perf_counter_ns()
                #self.update_runtime()
                self.current_running_proc.update_virtual_deadline()
                self.add_proc_ready_queue(self.current_running_proc)
            elif self.current_running_proc.status == TaskStatus.BLOCKED:
                #Add to whatever blocked queue, sleep, I/O queue.
                #self.add_proc_blocked_queue(self.current_running_proc)
                pass
            elif self.current_running_proc.status == TaskStatus.EXIT:
                # Do not need to do anything, it is basically dead. (Free allocated memory etc..)
                print(f"{self.current_running_proc.pid} EXITED")
            else:
                print("Unknown status")

            if self.deadline_queue:
                #Schedule Deadline
                pass
            elif not self.is_bitmap_empty():
                # Schedule Real Time
                print("SCHEDULING NEXT")
                self.current_running_proc = self.queue_next_proc()
            elif self.red_black_tree.root is not None:
                # Schedule Fair with CFS or EEVDF

                self.current_running_proc = self.red_black_tree.get_next_process()
            else:
                if self.idle_queue:
                    pass
                    #Run the idle threads I guess
                print("Nothing to schedule...Not even in the idle queue, guess something is wrong")

            print(self.current_running_proc.pid)
            if self.current_running_proc.green.dead:
                raise GreenletDeadError("Greenlet is dead, this is not supposed to happen, the greenlet should call exit!")
            self.current_running_proc.green.switch()  # Resume execution

    def make_sim_FIFO(self, num):
        for i in range(num):
            self.add_proc_ready_queue(MathYieldProcess(i, 50 ,Policy.SCHED_FIFO))
        self.add_proc_ready_queue(MathYieldProcess(num, 30, Policy.SCHED_FIFO))
        self.current_running_proc = MathYieldProcess(num + 1, 50, Policy.SCHED_FIFO)
        self.schedule_next_process()


    def make_sim_RR(self, num):
        for i in range(num):
            self.add_proc_ready_queue(CPUHeavyProc(i, Policy.SCHED_RR))
        self.current_running_proc = CPUHeavyProc(num + 1, Policy.SCHED_FIFO)
        self.schedule_next_process()
















