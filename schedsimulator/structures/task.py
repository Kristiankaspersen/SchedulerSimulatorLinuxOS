import random

import greenlet

from schedsimulator.enqueue_task import enqueue_entity
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.task_type import TaskType


class Task:
    cpu_offset = 0
    interactive_offset = 0
    number_of_tasks = 0 # Not sure if I am using this.
    def __init__(self, type, pid):
        self.pid = pid
        self.greenlet = greenlet.greenlet(self.run)  # Create a greenlet for this process
        self.type = type
        self.exec_start = 0
        self.custom_slice = False
        self.deadline = 0
        self.vruntime = 1
        self.slice = 0
        self.vlag = 0
        self.on_rq = 0
        self.prev_sum_exec_runtime = 0
        # This is the sum of the entire runtime right.
        self.sum_exec_runtime = 0
        self.rb_node = None
        self.status = TaskStatus.NEW
        self.weight = 1024
        # Think about how this is going to be
        self.tick_offset = 0



        ### Not going to include, but for test now.
        # ----- Unique props for this process ------
        #self.cpu_work = random.randint(10000, 1000000)
        self.tick_count = 0
        self.cpu_work = 100000000
        self.other_number = self.cpu_work // 10
        self.other_number = 1000000

        # STATS
        self.min_vruntime = 0
        self.enqueue_time = 0
        self.enqueue_time_virtual = 0
        self.latency = 0



    def run(self, interrupt_tick):
        """Simulated CPU-bound task that gets preempted."""
        # print(f"▶️ Process {self.pid} started.")

        if self.type == TaskType.CPU:
            print(f"CPU: {self.pid}")
            compute = 0
            while self.tick_count <= 400:
                compute += 1
            print(self.tick_count)
            interrupt_tick.enabled = False
            self.status = TaskStatus.EXIT
            greenlet.getcurrent().parent.switch()
        elif self.type == TaskType.RESP:
            print(f"RESP: {self.pid}")
            compute = 0
            while self.tick_count <= 300:
                compute += 1
                #print(self.tick_count)
                #if self.status  == TaskStatus.BLOCKED:
                    #self.status.READY
                    #greenlet.getcurrent().parent.switch()

                if self.tick_count % 2 == 0:
                    interrupt_tick.enabled = False
                    self.status = TaskStatus.BLOCKED
                    greenlet.getcurrent().parent.switch()

            print(self.tick_count)
            interrupt_tick.enabled = False
            self.status = TaskStatus.EXIT
            greenlet.getcurrent().parent.switch()
        else:
            print(f"IO: {self.pid}")
            compute = 0
            while self.tick_count <= 10:
                compute += 1

                if self.tick_count % 10 == 0:
                    interrupt_tick.enabled = False
                    self.status = TaskStatus.BLOCKED
                    greenlet.getcurrent().parent.switch()

            print(self.tick_count)
            interrupt_tick.enabled = False
            self.status = TaskStatus.EXIT
            greenlet.getcurrent().parent.switch()


    # First test task, its CPU heavy.
    # def run(self, cfs_rq, start_tasks):
    #     """Simulated CPU-bound task that gets preempted."""
    #     # print(f"▶️ Process {self.pid} started.")
    #     compute = 0
    #     while self.tick_count <= 10:
    #         compute += 1
    #
    #
    #
    #     #computing =0
    #     # for i in range(self.cpu_work):  # Simulating CPU work
    #     #     computing += i
    #     #     #print(f"Doing work {self.pid}")
    #     #     #if i == 100:
    #     #     #    print(f"Doing work {self.pid}")
    #     #     #if i == 1000:
    #     #     #    self.status = PCBStatus.BLOCKED
    #     #     #    greenlet.getcurrent().parent.switch()
    #     #     if Task.number_of_tasks != start_tasks:
    #     #         Task.number_of_tasks += 1
    #             #enqueue_entity(cfs_rq, Task(TaskType.CPU, random.randint(10000, 100000000)))
    #
    #
    #     # print(f" Process {self.pid} finished execution.")
    #     print(f"EXIT{TaskStatus.EXIT}")
    #     self.status = TaskStatus.EXIT
    #     greenlet.getcurrent().parent.switch()


