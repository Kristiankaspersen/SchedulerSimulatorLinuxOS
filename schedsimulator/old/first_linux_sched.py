import signal

from schedsimulator.Exceptions.greenletDeadExc import GreenletDeadError
from schedsimulator.enums.process_status import TaskStatus


class Task:
    def __init__(self, name, priority, time_slice):
        self.name = name
        self.priority = priority
        self.time_slice = time_slice
        self.remaining_time_slice = time_slice

    def __repr__(self):
        return f"{self.name}(P={self.priority}, TS={self.remaining_time_slice})"

    def goodness(self):
        if self.remaining_time_slice == 0:
            return 0
        return self.priority + self.remaining_time_slice

class OnScheduler:
    def __init__(self):
        self.ready_queue = []
        signal.signal(signal.SIGALRM, self.schedule_tick)
        signal.setitimer(signal.ITIMER_REAL, 0.1, 0.1)  # 100ms time slice
        self.current_running_proc = None
        self.current_tick = 0

    def schedule_tick(self, signum, frame):
        print(f"\n[Tick {self.current_tick}]")
        self.current_tick += 1

        # Find the task with the highest goodness
        flag = True
        while flag:
            best_task = None
            max_goodness = -1
            for task in self.ready_queue:
                g = task.goodness()
                if g > max_goodness:
                    max_goodness = g
                    best_task = task

            # If all tasks have 0 time slice left, reset time slices
            if best_task is None or best_task.remaining_time_slice == 0:
                print("→ All tasks out of time slice. Recharging...")
                for task in self.ready_queue:
                    task.remaining_time_slice = task.time_slice
                # I have to do the above again
            else:
                flag = False

        # Run the best task for one tick
        print(f"→ Running {best_task.name} (goodness = {best_task.goodness()})")
        best_task.remaining_time_slice -= 1
        self.current_running_proc.green.switch()

        # Show task states
        print("  Task states:", tasks)

    def scheduler(self):
        pass























        # Before this I need a function that puts current running in the correct ready queue.
        # Put current running
        while True:
            if self.current_running_proc.status == TaskStatus.NEW:
                self.enqueue_task(self.current_running_proc)
            elif self.current_running_proc.status == TaskStatus.READY:
                self.enqueue_task(self.current_running_proc)
            elif self.current_running_proc.status == TaskStatus.BLOCKED:
                # Add to whatever blocked queue, sleep, I/O queue.
                # self.add_proc_blocked_queue(self.current_running_proc)
                pass
            elif self.current_running_proc.status == TaskStatus.EXIT:
                # Do not need to do anything, it is basically dead. (Free allocated memory etc..)
                print(f"{self.current_running_proc.pid} EXITED")
            else:
                print("Unknown status")

            self.current_running_proc = self.pick_next_task()

            # Run the idle threads I guess
            print("Nothing to schedule...Not even in the idle queue, guess something is wrong")

            print(self.current_running_proc.pid)
            if self.current_running_proc.green.dead:
                raise GreenletDeadError(
                    "Greenlet is dead, this is not supposed to happen, the greenlet should call exit!")
            self.current_running_proc.green.switch()  # Resume execution

    def enqueue_task(self, process):
        pass

    def dequeue_task(self, process):
        pass

    def yield_task(self, process):
        pass

    def pick_next_task(self):
        process = None

        return process

    def put_prev_task(self):
        pass




    def schedule_next_process(self):


