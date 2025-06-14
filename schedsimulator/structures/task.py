import random

import greenlet

from schedsimulator.enqueue_task import enqueue_entity
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.task_type import TaskType


class Task:
    cpu_offset = 0
    interactive_offset = 0
    number_of_tasks = 0  # Not sure if I am using this.

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
        # self.cpu_work = random.randint(10000, 1000000)
        self.tick_count = 0
        self.cpu_work = 100000000
        self.other_number = self.cpu_work // 10
        self.other_number = 1000000

        # STATS
        self.min_vruntime = 0
        self.enqueue_time = 0
        self.enqueue_time_virtual = 0
        self.latency = 0
        self.last_spawn_tick = 1000000

    def run(self, cfs_rq, interrupt_tick):

        if self.type == TaskType.CPU:
            compute = 0
            while self.tick_count <= 1200:
                compute += 1
                # print(self.pid)
                # print(self.status)
                # print(cfs_rq.nr_queued)

                # if self.tick_count % 100 == 0 and self.tick_count != self.last_spawn_tick:
                #     if cfs_rq.num_interactive == 0:
                #         print("How many are added")
                #         new_task = Task(TaskType.RESP, self.tick_count + 100)
                #         enqueue_entity(cfs_rq, new_task)
                #         print(cfs_rq.num_interactive)
                #         self.last_spawn_tick = self.tick_count

            # cpu_work = 0
            # while cpu_work <= self.cpu_work:
            #     cpu_work += 1
            # print(cpu_work)
            print(self.tick_count)
            interrupt_tick.enabled = False
            self.status = TaskStatus.EXIT
            greenlet.getcurrent().parent.switch()
        elif self.type == TaskType.RESP:
            compute = 0
            while self.tick_count <= 300:
                compute += 1
                # print("this runs")
                # print(self.tick_count)
                # if self.status  == TaskStatus.BLOCKED:
                # self.status.READY
                # greenlet.getcurrent().parent.switch()

                if self.tick_count % 3 == 0:
                    interrupt_tick.enabled = False
                    self.status = TaskStatus.BLOCKED
                    greenlet.getcurrent().parent.switch()

            interrupt_tick.enabled = False
            self.status = TaskStatus.EXIT
            greenlet.getcurrent().parent.switch()
        else:
            compute = 0
            while self.tick_count <= 300:
                compute += 1

                if self.tick_count % 10 == 0:
                    interrupt_tick.enabled = False
                    self.status = TaskStatus.BLOCKED
                    greenlet.getcurrent().parent.switch()

            interrupt_tick.enabled = False
            self.status = TaskStatus.EXIT
            greenlet.getcurrent().parent.switch()

    # First test task, its CPU heavy.
    # def run(self, cfs_rq, start_tasks):
    #     """Simulated CPU-bound task that gets preempted."""
    #     # print(f" Process {self.pid} started.")
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
