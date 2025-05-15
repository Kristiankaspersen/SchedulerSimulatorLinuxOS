import heapq
import signal
import time
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
from schedsimulator.tabular_q_learner import seed_q_table, learn_on_preempt, bucket_interactive
from schedsimulator.task_tick import task_tick_fair
from schedsimulator.wakeup_preempt import wakeup_preempt
from schedsimulator.structures.task import Task
from schedsimulator.globals import TICK_NSEC, TICK_SEC, INIT_TREE
import schedsimulator.globals as globals


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

    def calculate_avg_preempt(self, preempt_intervals):
        return sum(preempt_intervals) / len(preempt_intervals) if preempt_intervals else 0
    def calculate_avg_latency(self, latencies):
        return sum(latencies) / len(latencies) if latencies else 0

    def learn(self):
        if self.cfs_rq.curr.type == TaskType.CPU:
            number_of_ticks = self.cfs_rq.virtual_global_clock_ns - self.cfs_rq.curr.tick_offset
            self.cfs_rq.cpu_preempt_intervals.append(number_of_ticks)

        avg_cpu_preempt = self.calculate_avg_preempt(self.cfs_rq.cpu_preempt_intervals)
        avg_latency = self.calculate_avg_latency(self.cfs_rq.resp_latencies_virtual)
        learn_on_preempt(self.q_table, self.cfs_rq.num_interactive, self.cfs_rq.num_cpu, avg_latency, avg_cpu_preempt)


    def check_wakeups(self):
        #print("Heap state before wakeup check:", list(self.sleeping_tasks_heap))
        resched = False
        while self.sleeping_tasks_heap and self.sleeping_tasks_heap[0][0] <= self.cfs_rq.virtual_global_clock_ns:
            _, _, task = heapq.heappop(self.sleeping_tasks_heap)
            #print(f"Waking task {task.pid}")
            task.state = TaskStatus.READY
            resched = wakeup_preempt(self.cfs_rq, task)
            #self.add_proc_ready_queue(task)

        #print("Heap state after wakeup check:", list(self.sleeping_tasks_heap))
        return resched

    def block_task(self, task):
        """Set sleep time for interactive and IO tasks and put the task in the blocked queue"""
        wakeup_tick = self.cfs_rq.virtual_global_clock_ns + (3 if task.type == TaskType.RESP else 10)
        heapq.heappush(self.sleeping_tasks_heap, (wakeup_tick, task.pid, task))

    def preempt_handler(self, signum, frame):
        """Handles preemption by switching back to the scheduler."""
        resched = False
        self.cfs_rq.virtual_global_clock_ns += TICK_NSEC
        # Learn every 5 ticks
        if globals.ADAPTIVE and self.cfs_rq.virtual_global_clock_ns % (5 * TICK_NSEC) == 0:
            self.learn()

        resched = self.check_wakeups()
        if self.cfs_rq.curr is not None:
            self.cfs_rq.curr.tick_count += 1
            self.cfs_rq.curr.status = TaskStatus.READY
        #self.cfs_rq.curr.tick_count += 1
            if not self.disable_tick_interrupt.enabled and self.is_preemptible(self.cfs_rq.curr):
                # Explicitly switch back to the scheduler
                #print(f"\nTimer-preempt on task pid: {self.cfs_rq.curr.pid}:")
                #print(f"   Values before update_curr(): deadline: {self.cfs_rq.curr.deadline}, vruntime: {self.cfs_rq.curr.vruntime}")
                if resched:
                    #assert False
                    self.preemptions += 1

                    #if globals.ADAPTIVE:
                    #    self.learn()
                    # print(f"   Values after update_curr(): deadline: {self.cfs_rq.curr.deadline}, vruntime: {self.cfs_rq.curr.vruntime}")
                    # print(f"Current min_vruntime in cfs_rq (runqueue): {self.cfs_rq.min_vruntime}")
                    # print(f"Global clock tick: {self.cfs_rq.virtual_global_clock_ns}\n")
                    self.cfs_rq.curr.greenlet.parent.switch()

                elif task_tick_fair(self.cfs_rq): # Check slice expiration
                    #assert False
                    self.preemptions += 1

                    #if globals.ADAPTIVE:
                    #    self.learn()

                    # print(f"   Values after update_curr(): deadline: {self.cfs_rq.curr.deadline}, vruntime: {self.cfs_rq.curr.vruntime}")
                    # print(f"Current min_vruntime in cfs_rq (runqueue): {self.cfs_rq.min_vruntime}")
                    # print(f"Global clock tick: {self.cfs_rq.virtual_global_clock_ns}\n")
                    self.cfs_rq.curr.greenlet.parent.switch()

            # If curr is None, nothing to switch — CPU is idle


    def is_preemptible(self, task):
        return task.status in (TaskStatus.NEW, TaskStatus.READY)





    def schedule(self):
        signal.signal(signal.SIGALRM, self.preempt_handler)
        signal.setitimer(signal.ITIMER_REAL, TICK_SEC, TICK_SEC)
        # IMPORTANT
        # TODO: Think about resched and stuff like that, in dequeue, how do I handle that
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


                if prev.status == TaskStatus.BLOCKED:
                    self.block_count += 1
                    prev.tick_count +=1

                    #if self.block_count == 10000:
                    #    break

                    self.block_task(prev) #Block the task.
                    dequeue_entity(self.cfs_rq, prev) # This will not remove anything from task_timeline (removed when setting next task)
                    # But still wee need to call update_entity_lag, thats why we do it.

                if prev.status == TaskStatus.EXIT:
                    print(f"task: {prev.pid} EXITED")
                    self.update_exit_count(prev)
                    self.cfs_rq.virtual_global_clock_ns += TICK_NSEC
                    #self.pid_count += 1
                    #new_task = Task(TaskType.CPU, self.pid_count)
                    #enqueue_entity(self.cfs_rq, new_task)
                    if prev.on_rq:
                        dequeue_entity(self.cfs_rq, prev) #Still need to update min_vruntime before enqueueing


                next = pick_next_task_fair(self.cfs_rq, prev)

                if self.exit_count == 20:
                    # Who cares about this tick count now? TODO: DELETE IT. (self.tick_count)
                    #self.tick_count = self.cfs_rq.curr.tick_count
                    break

                if next is None:
                    self.enable_interrupts()
                    print(self.cfs_rq.nr_queued)
                    #self.cfs_rq.task_timeline.print_tree()
                    #break
                    continue



                if next.greenlet.dead:
                    print(f"What process is dead? PID: {next.pid} Type: {next.type}, {next.tick_count}")
                    raise GreenletDeadError("Greenlet is dead, this is not supposed to happen, the greenlet should call exit!")

                self.enable_interrupts()
                next.greenlet.switch(self.disable_tick_interrupt)  # Resume execution
                self.disable_interrupts()
            else:
                self.enable_interrupts()
                #break
                if self.cfs_rq.nr_queued > 0:
                    self.disable_interrupts()
                    # Schedule Real Time
                    #self.cfs_rq.curr = pick_eevdf(self.cfs_rq)
                    next = pick_next_task_fair(self.cfs_rq, None)
                    self.enable_interrupts()
                    next.greenlet.switch(self.disable_tick_interrupt)  # Resume execution
                    self.disable_interrupts()



        #except KeyboardInterrupt:
        #    print("end program")
        #finally:

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
        print(f"tick_count: {self.tick_count}")


        throughput = 0
        # Throughput calculation
        if self.real_now > 0:
            throughput = self.exit_count / (self.real_now / 1_000_000_000)
            print(f"Avg throughput: {throughput:.7f} tasks per second")
        else:
            print("Avg throughput: (time too short to measure)")

        avg_latency = 0
        if self.cfs_rq.latencies:
            avg_latency = sum(self.cfs_rq.latencies) / len(self.cfs_rq.latencies)
            print(f"Average latency: {avg_latency / 1_000_000:.3f} ms")


        print(self.preemptions)
        print(throughput)
        print(avg_latency)


        return self.preemptions, throughput, avg_latency




    def make_sim_eevdf(self, num):
        globals.INIT_TREE = False
        globals.initial_vr_diff = 0
        globals.initial_deadline_diff = 0
        self.pid_count = 0
        #self.cfs_rq.curr = Task(TaskType.CPU, self.pid_count)
        #enqueue_entity(self.cfs_rq, self.cfs_rq.curr)
        for i in range(num):
            self.pid_count += 1
            if i % 3 == 0:
                enqueue_entity(self.cfs_rq, Task(TaskType.RESP, self.pid_count))
            elif i % 2 == 0:
                enqueue_entity(self.cfs_rq, Task(TaskType.RESP, self.pid_count))
            else:
                enqueue_entity(self.cfs_rq, Task(TaskType.RESP, self.pid_count))

        # for _ in range(num):
        #     self.pid_count += 1
        #     enqueue_entity(self.cfs_rq, Task(TaskType.CPU, self.pid_count))

        return self.schedule()




























