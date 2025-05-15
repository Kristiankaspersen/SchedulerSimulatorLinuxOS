import os
import signal
import time
from multiprocessing import Queue, Pipe, Process
import heapq
from queue import Empty

import greenlet

from schedsimulator.Exceptions.greenletDeadExc import GreenletDeadError
from schedsimulator.enums.task_type import TaskType
from schedsimulator.processes.cpu_heavy_proc import GreenletProc
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.process_policy import Policy
from schedsimulator.processes.cpu_heavy_proc2 import CPUHeavyProc
from schedsimulator.processes.math_yield_proc2 import MathYieldProcess
from schedsimulator.structures.red_black_tree import RedBlackTree


# Test this as round robin scheduler....
PREEMPT_TIME = 10
class RRScheduler:
    MAX_RT_PRIORITIES = 100

    def __init__(self):
        #self.hardware_queue = Queue()
        self.sleeping_tasks_heap = []
        self.ready_queue = []
        self.current_running_proc = None
        self.preempt_timer_enable_interrupt = False
        self.virtual_global_clock_ns = 0
        self.exit_count = 0
        self.block_count = 0

    def check_wakeups(self):
        print("Heap state before wakeup check:", list(self.sleeping_tasks_heap))
        while self.sleeping_tasks_heap and self.sleeping_tasks_heap[0][0] <= self.virtual_global_clock_ns:
            _, _, task = heapq.heappop(self.sleeping_tasks_heap)
            print(f"Waking task {task.pid}")
            self.add_proc_ready_queue(task)

        print("Heap state after wakeup check:", list(self.sleeping_tasks_heap))

    def block_task(self, process):
        wakeup_tick = self.virtual_global_clock_ns + (5 if process.type == TaskType.RESP else 10)
        heapq.heappush(self.sleeping_tasks_heap, (wakeup_tick, process.pid, process))



    def preempt_handler(self, signum, frame):
        """Handles preemption by switching back to the scheduler."""
        # 1. Advance global virtual time
        self.virtual_global_clock_ns += 1
        # 2. Send updated tick to hardware process
        self.check_wakeups()

        if not self.preempt_timer_enable_interrupt and self.current_running_proc is not None:
            # 3. Advance task time
            self.current_running_proc.tick_count += 1

            # 4. Preempt if needed
            if self.current_running_proc.tick_count % PREEMPT_TIME == 0:
                self.current_running_proc.status = TaskStatus.READY
                self.current_running_proc.green.parent.switch()

    def add_proc_ready_queue(self, process):
            # Add to FIFO Ready queues
            process.status = TaskStatus.READY
            self.ready_queue.append(process)

    def queue_next_proc(self):
        return self.ready_queue.pop(0)

    def schedule_next_process(self):
        #signal.signal(signal.SIGUSR1, self.wakeup_handler)

        signal.signal(signal.SIGALRM, self.preempt_handler)
        signal.setitimer(signal.ITIMER_REAL, 0.01, 0.01)  # 100ms time slice
        # 1️⃣ Set up hardware process and signal handling (if not already done)
        while True:
            #if self.current_running_proc is not None:
            #    self.disable_interrupts()
            if self.current_running_proc is not None:
                self.preempt_timer_enable_interrupt = True
                if  self.current_running_proc.status == TaskStatus.NEW:
                    self.add_proc_ready_queue(self.current_running_proc)
                elif self.current_running_proc.status == TaskStatus.READY:
                    self.add_proc_ready_queue(self.current_running_proc)
                elif self.current_running_proc.status == TaskStatus.BLOCKED:
                    self.block_count += 1

                    print(f"{self.current_running_proc.pid} BLOCK")
                    self.current_running_proc.tick_count += 1
                    #self.virtual_global_clock_ns += 1
                    self.block_task(self.current_running_proc)

                elif self.current_running_proc.status == TaskStatus.EXIT:
                    # Do not need to do anything, it is basically dead. (Free allocated memory etc..)
                    #self.virtual_global_clock_ns += 1
                    self.exit_count += 1
                    if self.exit_count == 10:
                        print(f"Block count: {self.block_count}")
                        break
                    print(f"{self.current_running_proc.pid} EXITED")
                else:
                    print("Unknown status")

                if len(self.ready_queue) > 0:
                    # Schedule Real Time
                    self.current_running_proc = self.queue_next_proc()
                else:
                    self.current_running_proc = None

                if self.current_running_proc is not None:
                    if self.current_running_proc.green.dead:
                        raise GreenletDeadError(
                            "Greenlet is dead, this is not supposed to happen, the greenlet should call exit!")

                    self.preempt_timer_enable_interrupt = False
                    # Re-enable interrupts after critical section
                    #self.enable_interrupts()
                    self.current_running_proc.green.switch()  # Resume execution

            else:
                self.preempt_timer_enable_interrupt = False
                if len(self.ready_queue) > 0:
                    print("DOES THIS EVER HAPPEN?!?!?!?!?!??!?!?!?!?!=!=!==!==!njsdfandjasndjisandlisandjka")
                    # Schedule Real Time
                    self.current_running_proc = self.queue_next_proc()
                    print(self.current_running_proc)


        # self.hardware_queue.put('STOP')
        # self.hw_proc.terminate()
        # self.hw_proc.join()


    def make_sim_FIFO(self, num):
        for i in range(num):
            self.add_proc_ready_queue(MathYieldProcess(i, 50 ,Policy.SCHED_FIFO))
        self.add_proc_ready_queue(MathYieldProcess(num, 30, Policy.SCHED_FIFO))
        self.current_running_proc = MathYieldProcess(num + 1, 50, Policy.SCHED_FIFO)
        self.schedule_next_process()


    def make_sim_RR(self, num):
        for i in range(num):
            if i % 3 == 0:
                self.add_proc_ready_queue(CPUHeavyProc(TaskType.CPU, i, Policy.SCHED_RR))
            elif i % 2 == 0:
                self.add_proc_ready_queue(CPUHeavyProc(TaskType.RESP, i, Policy.SCHED_RR))
            else:
                self.add_proc_ready_queue(CPUHeavyProc(TaskType.IO, i, Policy.SCHED_RR))

        self.current_running_proc = CPUHeavyProc(TaskType.CPU, num + 1, Policy.SCHED_FIFO)
        self.schedule_next_process()
















    # def disable_interrupts(self):
    #     # Block both SIGUSR1 and SIGALRM (adjust if needed)
    #     self._signals_to_block = {signal.SIGUSR1, signal.SIGALRM}
    #     self._old_signal_mask = signal.pthread_sigmask(signal.SIG_BLOCK, self._signals_to_block)
    #     #print("[Scheduler] Interrupts disabled")
    #
    # def enable_interrupts(self):
    #     # Restore previous signal mask
    #     signal.pthread_sigmask(signal.SIG_SETMASK, self._old_signal_mask)
    #     #print("[Scheduler] Interrupts enabled")




    # def wakeup_handler2(self, signum, frame):
    #     self.disable_interrupts()  # Block other signals immediately
    #     if self.scheduler_end.poll():  # Check if there's data
    #         task_id = self.scheduler_end.recv()
    #         print(f"[Scheduler] Waking up task {task_id}")
    #         task = self.sleeping_tasks.pop(task_id, None)
    #         if task:
    #             task.status = TaskStatus.READY
    #             self.add_proc_ready_queue(task)
    #         else:
    #             print(f"[Scheduler] WARNING: Task {task_id} not found in sleeping_tasks")
    #     self.enable_interrupts()


    # def setup_hardware_process(self):
    #
    #     # Pipe to send ticks from scheduler -> hardware
    #     self.scheduler_to_hw_pipe, self.hw_clock_receiver_pipe = Pipe()
    #
    #     # Pipe to send wakeup task IDs from hardware -> scheduler
    #     self.scheduler_end, self.hardware_end = Pipe()
    #
    #     self.hw_proc = Process(
    #         target=self.hardware_process,
    #         args=(
    #             os.getpid(),
    #             self.hardware_queue,  # task block requests
    #             self.hardware_end,  # pipe to send back wakeup task ID
    #             self.hw_clock_receiver_pipe  # pipe to receive ticks
    #         )
    #     )
    #
    #     self.hw_proc.start()

    # def hardware_process(self, scheduler_pid, queue, wakeup_pipe, clock_pipe):
    #     import heapq, os, signal
    #     from queue import Empty
    #
    #     heap = []
    #     print(f"[Hardware] Started (PID {os.getpid()}) → tick-based mode")
    #
    #     while True:
    #         # Fetch any new wakeup requests
    #         try:
    #             while True:
    #                 task_info = queue.get_nowait()
    #                 if task_info == 'STOP':
    #                     print("[Hardware] Shutting down")
    #                     return
    #                 wakeup_tick = task_info['wakeup_tick']
    #                 task_id = task_info['task_id']
    #                 heapq.heappush(heap, (wakeup_tick, task_id))
    #                 print(f"[Hardware] Task {task_id} scheduled at tick {wakeup_tick}")
    #         except Empty:
    #             pass
    #
    #         # Get new tick from scheduler
    #         if clock_pipe.poll():
    #             current_tick = clock_pipe.recv()
    #             print(f"[Hardware] Tick received: {current_tick}")
    #
    #             while heap and heap[0][0] <= current_tick:
    #                 _, task_id = heapq.heappop(heap)
    #                 print(f"[Hardware] Waking task {task_id} at tick {current_tick}")
    #                 wakeup_pipe.send(task_id)
    #                 os.kill(scheduler_pid, signal.SIGUSR1)














