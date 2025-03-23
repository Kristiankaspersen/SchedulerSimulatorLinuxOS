import signal
import time

from schedsimulator.Exceptions.greenletDeadExc import GreenletDeadError
from schedsimulator.processes.cpu_heavy_proc import GreenletProc
from schedsimulator.structures.process_status import PCBStatus


class RoundRobinGreenlet:
    def __init__(self, num_processes):
        # Inits a roundrobin queue with num_processes.
        # I am going for min-heap for the I/O queues as well, because we are going to simulate them based on time in our simulation.
        self.io_wait_queues = {  # Separate queues for each I/O device
            "disk": [],
            "network": [],
            "usb": [],
        }
        self.sleep_queue = []  # Only thing i need to do, is push to the list, with use of heapq. Then I will get an min-max for sleep.
        process = GreenletProc(0)
        self.current_process = process
        for i in range(num_processes - 1):
            process.next = GreenletProc(i + 1)  # Next is new node
            process.next.prev = process  # New node prev is the old process
            process = process.next  # Then update the new process to be the old for the next iteration.
        # What is the last process now
        self.current_process.prev = process
        process.next = self.current_process
        # current process is the first in the queue, that is going to start.
        # Go through the queue, and check if everything is correct.
        self.processes_in_ready_queue = num_processes
        current = self.current_process
        for i in range(self.processes_in_ready_queue):
            print(current.pid)
            current = current.prev

        signal.signal(signal.SIGALRM, self.preempt_handler)
        signal.setitimer(signal.ITIMER_REAL, 0.1, 0.1)  # 100ms time slice

    def preempt_handler(self, signum, frame):
        """Handles preemption by switching back to the scheduler."""
       # print(f"SIGALRM received! Preempting process {self.current_process.pid}")

        self.current_process.status = PCBStatus.READY

        # Explicitly switch back to the scheduler
        self.current_process.green.parent.switch()

    def scheduler(self):

        while self.current_process is not None:
            match self.current_process.status:
                case PCBStatus.NEW:
                    #print("STATUS NEW, sched")
                    self.current_process.status = PCBStatus.READY
                case PCBStatus.READY:
                    #print("STATUS READY, sched, preempt")
                    self.current_process = self.current_process.next
                    ## This is the only place where I do something with the ready queue in the scheduler
                case PCBStatus.EXIT:
                    print("STATUS EXIT, sched")
                    # Remove process is a part of linked list ready queue
                    self.remove_process()
                case PCBStatus.BLOCKED:
                    print("STATUS BLOCKED sched")
                    # Is it possible to just do the blocking here.
                    # Do nothig here, since it is been blocked, and when a process is removed, we schedule the next to be current running.
                case PCBStatus.RUNNING:
                    print("Just keep running")
                case _:
                    # Unknown
                    print("Noob")

            #print(f"Current number of processes in queue {self.processes_in_ready_queue}")
            current = self.current_process
            current_proceeses = []
            for i in range(self.processes_in_ready_queue):
                current_proceeses.append(current.pid)
                current = current.next
            #print(current_proceeses)
            if self.current_process is not None:
                # So here the dispather will run, but since this is higher level, there is no need for the dispatcher
                # And we wil just simulate that with running the correct process.

                if self.current_process.green.dead:
                    raise GreenletDeadError("Greenlet is dead, this is not supposed to happen, the greenlet should call exit!")
                self.current_process.green.switch(self)  # Resume execution
            else:
                # So this will always happen when exit is called, since then the last one is removed.
                # So now the program just stops when there are no more threads left, is this what I want? Or a halt?
                # But then again how am I supposed to measure.
                print("The READY queue is empty, and will eventually stop......")
        else:
            print("The READY queue is empty, and the scheduler has stopped")
            # Wait for new processes to start running again.

    def non_blocking_sleep(self, seconds):
        start_time = time.time()  # Get current time
        while time.time() - start_time < seconds:
            pass


    def exit(self):
        self.current_process.status = PCBStatus.EXIT

    def yields(self):
        self.current_process.status = PCBStatus.READY

    def block(self, blocked_queue):
        # Put current process in blocked queue
        self.current_process.status = PCBStatus.BLOCKED
        removed_process = self.remove_process()
        blocked_queue.push(removed_process)

    def unblock(self, blocked_queue):
        # Unblock first process in blocked queue
        self.add_process(blocked_queue.pop())

    def remove_process(self):
        # Need to deal with empty queue,
        # Also with queue that is two left I guess.
        if not self.current_process:
            return None  # Nothing to remove

        removed_process = self.current_process

        if self.current_process.next == self.current_process:  # only one process in queue.
            self.current_process = None  # Now the queue is empty
        else:
            # Update the new links in list.
            self.current_process.next.prev = self.current_process.prev
            self.current_process.prev.next = self.current_process.next
            # Move to the next process
            self.current_process = self.current_process.next

        # Disconnect removed process
        removed_process.next = None
        removed_process.prev = None
        self.processes_in_ready_queue -= 1
        return removed_process

    def add_process(self, process):
        # I put it back in the ready queue here. I put it
        if PCBStatus.BLOCKED == process.status:
            process.status = PCBStatus.READY
        else:
            process.status = PCBStatus.NEW
        self.current_process.prev.next = process
        process.prev = self.current_process.prev
        self.current_process.prev = process
        process.next = self.current_process
        self.processes_in_ready_queue += 1

    # async def block_on_io(self, process, device):
    #     # TODO: Missing the block
    #     """Moves a process to the I/O queue and starts an I/O interrupt timer."""
    #     print(f"Process {process.pid} is blocked on {device} I/O.")
    #     io_time = random.uniform(1,
    #                              5)  # Simulate different I/O burst times, I want this to be different based on type of device.
    #     completion_time = time.time() + io_time
    #     removed_process = self.remove_process()
    #     # And then put it in again when
    #     # I am just using the event loop as my loop in the simulation, I do not need queues for this.
    #     heapq.heappushpop(self.io_wait_queues[device], (completion_time, process))
    #     asyncio.create_task(self.unblock_after(io_time, removed_process))
    #     return
    #
    # async def block_on_sleep(self, process, sleep_time):
    #     # TODO: Missing the block
    #     """Moves a process to the sleep queue."""
    #     wake_time = time.time() + sleep_time
    #     heapq.heappushpop(self.sleep_queue, (wake_time, process))
    #     print(f"Process {process.pid} is now sleeping for {sleep_time:.2f} seconds.")
    #     removed_process = self.remove_process()
    #     asyncio.create_task(self.unblock_after(sleep_time, removed_process))
    #     return

    # async def unblock_after(self, delay, process):
    #     await asyncio.sleep(delay)
    #     self.add_process(process)
    #     print(f"Process {process.pid} moved to READY queue.")
