import heapq
import random
import signal
import time
from collections import deque

import greenlet

from schedsimulator.Exceptions.greenletDeadExc import GreenletDeadError
from schedsimulator.dequeue_task import dequeue_entity
from schedsimulator.enqueue_task import enqueue_entity
from schedsimulator.enums.task_type import TaskType
from schedsimulator.pick_next_task_fair import pick_next_task_fair, pick_eevdf
from schedsimulator.processes.cpu_heavy_proc import GreenletProc
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.process_policy import Policy
from schedsimulator.processes.cpu_heavy_proc2 import CPUHeavyProc
from schedsimulator.processes.math_yield_proc2 import MathYieldProcess
from schedsimulator.structures.cfs_rq import CfsRunQueue
from schedsimulator.structures.red_black_tree import RedBlackTree
from schedsimulator.tabular_q_learner import seed_q_table, learn_on_preempt, bucket_interactive, learning_log
from schedsimulator.task_tick import task_tick_fair
from schedsimulator.wakeup_preempt import wakeup_preempt
from schedsimulator.structures.task import Task
from schedsimulator.globals import TICK_NSEC, TICK_SEC, INIT_TREE, EXIT_COUNT, INTERACTIVE_TIME_WINDOW, SLEEP_TIME_INTERACTIVE, SLEEP_TIME_IO, NUM_INTERACTIVE, NUM_CPU, NUM_IO
import schedsimulator.globals as globals
import pandas as pd


class TickControl:
    def __init__(self, enabled=True):
        self.enabled = enabled

class EEVDFScheduler:
    def __init__(self):
        #self.task_queue = [] # ready, starting point
        self.cfs_rq = CfsRunQueue()
        self.cfs_rq.curr = None
        self.wakeup_flag = False
        self.total_throughput = 0
        self.total_latency = 0
        self.avg_latency = 0
        self.avg_thoughput = 0
        self.exit_count = 0
        self.cpu_exit_count = 0
        self.resp_exit_count = 0
        self.io_exit_count = 0
        self.block_count = 0
        self.start_num_tasks = 10000
        self.disable_tick_interrupt = TickControl()
        self.baseline_ns = 0
        self.real_now = 0
        self.preemptions = 0
        self.pid_count = 0
        self.tick_count = 0
        self.q_table = seed_q_table()
        self.sleeping_tasks_heap = []
        self.cpu_throughput = 0

    def calculate_avg_preempt(self, preempt_intervals):
        return sum(preempt_intervals) / len(preempt_intervals) if preempt_intervals else 0
    def calculate_avg_latency(self, latencies):
        return sum(latencies) / len(latencies) if latencies else 0

    def count_recent_interactive(self, cfs_rq, window=5):
        now = self.cfs_rq.virtual_global_clock_ns
        return sum(
            1 for t in cfs_rq.runqueue
            if t.type == TaskType.RESP and t.enqueue_time_virtual >= now - window
        )

    def purge_old_interactive(self, window):
        while self.cfs_rq.interactive_arrivals and self.cfs_rq.interactive_arrivals[0] < self.cfs_rq.virtual_global_clock_ns - window:
            self.cfs_rq.interactive_arrivals.popleft()

    def get_recent_interactive_count(self):
        return len(self.cfs_rq.interactive_arrivals)


    def learn(self):

        interactive_count = self.get_recent_interactive_count()

        # Failsafe: if no recent interactivity, but interactive tasks are present
        if interactive_count == 0 and self.cfs_rq.num_interactive > 0:
            interactive_count = 1  # Treat as "very few"
            if self.cfs_rq.num_interactive > 1:
                interactive_count = 2  # Bucket: "moderete interactives"

        avg_cpu_preempt = self.calculate_avg_preempt(self.cfs_rq.cpu_preempt_intervals)
        avg_latency = self.calculate_avg_latency(self.cfs_rq.resp_latencies_virtual)
        learn_on_preempt(self.q_table, interactive_count, self.cfs_rq.num_cpu, avg_latency, avg_cpu_preempt)


    def check_wakeups(self):
        #print("Heap state before wakeup check:", list(self.sleeping_tasks_heap))
        resched = False
        while self.sleeping_tasks_heap and self.sleeping_tasks_heap[0][0] <= self.cfs_rq.virtual_global_clock_ns:
            _, _, task = heapq.heappop(self.sleeping_tasks_heap)
            #print(f"Waking task {task.pid}")
            task.status = TaskStatus.READY
            resched = wakeup_preempt(self.cfs_rq, task)

        #print("Heap state after wakeup check:", list(self.sleeping_tasks_heap))
        return resched

    def block_task(self, task):
        """Set sleep time for interactive and IO tasks and put the task in the blocked queue"""
        wakeup_tick = self.cfs_rq.virtual_global_clock_ns + (SLEEP_TIME_INTERACTIVE if task.type == TaskType.RESP else SLEEP_TIME_IO)
        heapq.heappush(self.sleeping_tasks_heap, (wakeup_tick, task.pid, task))

    def preempt_handler(self, signum, frame):
        """Handles preemption by switching back to the scheduler."""

        resched = False
        self.cfs_rq.virtual_global_clock_ns += TICK_NSEC
        # Learn every 5 ticks

        resched = self.check_wakeups()
        if self.cfs_rq.curr is not None:
            if globals.ADAPTIVE and self.cfs_rq.virtual_global_clock_ns % (5 * TICK_NSEC) == 0:
                self.purge_old_interactive(INTERACTIVE_TIME_WINDOW)

                self.learn()
            self.cfs_rq.curr.tick_count += 1
            self.cfs_rq.curr.status = TaskStatus.READY
            if not self.disable_tick_interrupt.enabled and self.is_preemptible(self.cfs_rq.curr):
                # Explicitly switch back to the scheduler
                if resched:
                    self.preemptions += 1

                    if self.cfs_rq.curr.type == TaskType.CPU:
                        number_of_ticks = self.cfs_rq.virtual_global_clock_ns - self.cfs_rq.curr.tick_offset
                        self.cfs_rq.cpu_preempt_intervals.append(number_of_ticks)

                    self.cfs_rq.curr.greenlet.parent.switch()

                elif task_tick_fair(self.cfs_rq): # Check slice expiration

                    self.preemptions += 1

                    if self.cfs_rq.curr.type == TaskType.CPU:
                        number_of_ticks = self.cfs_rq.virtual_global_clock_ns - self.cfs_rq.curr.tick_offset
                        self.cfs_rq.cpu_preempt_intervals.append(number_of_ticks)

                    self.cfs_rq.curr.greenlet.parent.switch()

            # If curr is None, nothing to switch — CPU is idle


    def is_preemptible(self, task):
        return task.status in (TaskStatus.NEW, TaskStatus.READY)



    def schedule(self):
        signal.signal(signal.SIGALRM, self.preempt_handler)
        signal.setitimer(signal.ITIMER_REAL, TICK_SEC, TICK_SEC)
        globals.INIT_TREE = False
        globals.cpu_offset = 0
        globals.interactive_offset = 0
        self.baseline_ns = time.time_ns()
        self.real_now = self.baseline_ns
        #try:
        while True:
            self.disable_interrupts()
            prev = None
            if self.cfs_rq.curr is not None:
                prev = self.cfs_rq.curr
                #Break for now I guess

                if prev.status == TaskStatus.NEW:
                    prev.status = TaskStatus.READY


                if prev.status == TaskStatus.BLOCKED:
                    self.block_count += 1
                    prev.tick_count +=1

                    self.block_task(prev) #Block the task.
                    dequeue_entity(self.cfs_rq, prev) # This will not remove anything from task_timeline (removed when setting next task)
                    # But still wee need to call update_entity_lag, thats why we do it.

                if prev.status == TaskStatus.EXIT:
                    print(f"task: {prev.pid} EXITED")
                    self.update_exit_count(prev)
                    self.cfs_rq.virtual_global_clock_ns += TICK_NSEC
                    self.pid_count += 1
                    if prev.on_rq:
                        dequeue_entity(self.cfs_rq, prev) #Still need to update min_vruntime before enqueueing

                    if self.cfs_rq.curr.type == TaskType.CPU:
                        if self.cpu_exit_count == NUM_CPU:
                            total_cpu_time_ns = time.time_ns() - self.baseline_ns
                            if total_cpu_time_ns > 0:
                                self.cpu_throughput = self.cpu_exit_count / (total_cpu_time_ns / 1_000_000_000)
                    if self.cfs_rq.curr.type == TaskType.IO:
                        if self.cpu_exit_count == NUM_CPU:
                            new_task = Task(TaskType.IO, self.pid_count)
                            enqueue_entity(self.cfs_rq, new_task)


                next = pick_next_task_fair(self.cfs_rq, prev)

                if self.exit_count == EXIT_COUNT:
                    break

                if next is None:
                    self.enable_interrupts()
                    continue

                if next.greenlet.dead:
                    print(f"What process is dead? PID: {next.pid} Type: {next.type}, {next.tick_count}")
                    raise GreenletDeadError("Greenlet is dead, this is not supposed to happen, the greenlet should call exit!")

                self.enable_interrupts()
                next.greenlet.switch(self.cfs_rq, self.disable_tick_interrupt)  # Resume execution
                self.disable_interrupts()
            else:
                self.enable_interrupts()
                if self.cfs_rq.nr_queued > 0:
                    self.disable_interrupts()
                    # Schedule Real Time
                    next = pick_next_task_fair(self.cfs_rq, None)
                    self.enable_interrupts()
                    next.greenlet.switch(self.cfs_rq, self.disable_tick_interrupt)  # Resume execution
                    self.disable_interrupts()

        return self.calculate_final_stats()




    def disable_interrupts(self):
        # Block both SIGUSR1 and SIGALRM (adjust if needed)
        #self._signals_to_block = {signal.SIGUSR1, signal.SIGALRM} # Block both timer and wakeup
        self.disable_tick_interrupt.enabled = True
        #self._signals_to_block = {signal.SIGUSR1} # Only block wakeup
        #self._old_signal_mask = signal.pthread_sigmask(signal.SIG_BLOCK, self._signals_to_block)
        #print("[Scheduler] Interrupts disabled")

    def enable_interrupts(self):
        # Restore previous signal mask
        self.disable_tick_interrupt.enabled = False
        #signal.pthread_sigmask(signal.SIG_SETMASK, self._old_signal_mask)
        #print("[Scheduler] Interrupts enabled")

    def update_exit_count(self, task):
        self.exit_count += 1
        if task.type == TaskType.CPU:
            self.cpu_exit_count += 1
        if task.type == TaskType.RESP:
            self.resp_exit_count += 1
        if task.type == TaskType.IO:
            self.resp_exit_count += 1


    def calculate_final_stats(self):
        self.real_now = time.time_ns() - self.baseline_ns
        print(f"Time the scheduler used:{self.real_now}")
        print(f"nr queued {self.cfs_rq.nr_queued}")
        print(f"exit count {self.exit_count}")
        print(f"block count {self.block_count}")
        print(f"Preemptions: {self.preemptions}")

        # General helper
        def avg_ns(latencies):
            return sum(latencies) / len(latencies) if latencies else 0

        # Initialize everything to 0
        avg_resp_latency = 0
        avg_cpu_latency = 0
        avg_io_latency = 0
        tot_avg_latency = 0
        tot_throughput = 0

        # Avg total latency
        if self.cfs_rq.latencies:
            tot_avg_latency = avg_ns(self.cfs_rq.latencies)
            print(f"Average latency (overall): {tot_avg_latency / 1_000_000:.3f} ms")


        # Interactive (RESP) latency
        if self.cfs_rq.resp_latencies:
            avg_resp_latency = avg_ns(self.cfs_rq.resp_latencies)
            print(f"Average latency (interactive - real): {avg_resp_latency / 1_000_000:.3f} ms")

        # CPU-bound latency
        if self.cfs_rq.cpu_latencies:
            avg_cpu_latency = avg_ns(self.cfs_rq.cpu_latencies)
            print(f"Average latency (CPU - real): {avg_cpu_latency / 1_000_000:.3f} ms")

            # I/O-bound
        if self.cfs_rq.io_latencies:
            avg_io_latency = avg_ns(self.cfs_rq.io_latencies)
            print(f"Average latency (I/O - real): {avg_io_latency / 1_000_000:.3f} ms")

        # Throughput calculation
        if self.real_now > 0:
            tot_throughput = self.exit_count / (self.real_now / 1_000_000_000)
            print(f"Avg throughput: {tot_throughput:.7f} tasks per second")
        else:
            print("Avg throughput: (time too short to measure)")


        # Save the learning log to CSV
        df = pd.DataFrame(learning_log)
        df.to_csv("learning_log.csv", index=False)

        # OK, now I need to return avg_io_latency, avg_cpu_latency, avg_resp_latency and self.cpu_throughput
        # Return all required stats
        # getattr(self, "cpu_throughput", 0)  # fallback to 0 if not yet set
        print(f"IO negative count: {globals.io_negative_count}")
        print(f"Interactive negative count: {globals.interactive_negative_count}")
        return (
            self.preemptions,
            tot_throughput,
            tot_avg_latency,
            avg_io_latency,
            avg_cpu_latency,
            avg_resp_latency,
            self.cpu_throughput
        )
        #return self.preemptions, tot_throughput, tot_avg_latency

    def make_sim_eevdf(self, num_resp=NUM_INTERACTIVE, num_io=NUM_IO, num_cpu=NUM_CPU, seed=None):
        globals.INIT_TREE = False
        globals.initial_vr_diff = 0
        globals.initial_deadline_diff = 0
        self.pid_count = 0

        # Create list of task types
        task_types = (
                [TaskType.RESP] * num_resp +
                [TaskType.IO] * num_io +
                [TaskType.CPU] * num_cpu
        )

        # Sanity check
        assert len(task_types) == (num_resp + num_io + num_cpu), "Mismatch in task count"

        if seed is not None:
            random.seed(seed)
            print(f"Shuffling tasks with seed: {seed}")

        # Shuffle for randomized enqueue order
        random.shuffle(task_types)

        for task_type in task_types:
            self.pid_count += 1
            enqueue_entity(self.cfs_rq, Task(task_type, self.pid_count))

        return self.schedule()




























