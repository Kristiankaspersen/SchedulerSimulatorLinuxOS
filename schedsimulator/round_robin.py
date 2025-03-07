import heapq
import random
import time
import asyncio
import inspect

from schedsimulator.processes.process import Process
from schedsimulator.structures.process_status import PCBStatus


class RoundRobin:
    def __init__(self, num_processes):
        # Inits a roundrobin queue with num_processes.
        # I am going for min-heap for the I/O queues as well, because we are going to simulate them based on time in our simulation.
        self.io_wait_queues = {  # Separate queues for each I/O device
            "disk": [],
            "network": [],
            "usb": [],
        }
        self.sleep_queue = []  # Only thing i need to do, is push to the list, with use of heapq. Then I will get an min-max for sleep.
        process = Process(0)
        self.current_process = process
        for i in range(num_processes - 1):
            process.next = Process(i + 1)  # Next is new node
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

    async def scheduler(self):
        while self.current_process is not None:
            match self.current_process.status:
                case PCBStatus.NEW:
                    print("STATUS NEW, sched")
                case PCBStatus.READY:
                    print("STATUS READY, sched, preempt")
                    self.current_process = self.current_process.next
                case PCBStatus.EXIT:
                    print("STATUS EXIT, sched")
                    self.remove_process()
                case PCBStatus.BLOCKED:
                    print("STATUS BLOCKED sched")
                    # Is it possible to just do the blocking here.
                case PCBStatus.RUNNING:
                    print("Just keep running")
                case _:
                    # Unknown
                    print("Noob")

            print(f"Current number of processes in queue {self.processes_in_ready_queue}")
            current = self.current_process
            current_proceeses = []
            for i in range(self.processes_in_ready_queue):
                current_proceeses.append(current.pid)
                current = current.next
            print(current_proceeses)
            if self.current_process is not None:
                # So here the dispather will run, but since this is higher level, there is no need for the dispatcher
                # And we wil just simulate that with running the correct process.
                # If new run
                if self.current_process.status == PCBStatus.NEW:
                    if inspect.isasyncgenfunction(self.current_process.run):
                        print("Does this happen??")
                        self.current_process.gen = self.current_process.run(self)
                        self.current_process.status = PCBStatus.READY
                        await anext(self.current_process.gen)
                    else:
                        await self.current_process.run(self)
                else:
                    if inspect.isasyncgenfunction(self.current_process.run):
                        try:
                            await anext(self.current_process.gen)  # Resume execution of each process
                        except StopIteration: #Switch to stopAsyncIteration when done, I just want this check here to make sure I exit in the last yield.
                            # If it ends up here, then remove it, since it is done. But should be exited earlier
                            # Just a chec
                            self.remove_process() # Remove finished processes
                    else:
                        await self.current_process.run(self)


                #
            else:
                # So this will always happen when exit is called, since then the last one is removed.
                # So now the program just stops when there are no more threads left, is this what I want? Or a halt?
                # But then again how am I supposed to measure.
                print("The READY queue is empty, and will eventually stop......")
        else:
            print("The READY queue is empty, and the scheduler has stopped")
            # Wait for new processes to start running again.

    def exit(self):
        self.current_process.status = PCBStatus.EXIT

    def yields(self):
        self.current_process.status = PCBStatus.READY

    def block(self, blocked_queue):
        # Put current process in blocked queue
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

    async def block_on_io(self, process, device):
        # TODO: Missing the block
        """Moves a process to the I/O queue and starts an I/O interrupt timer."""
        print(f"Process {process.pid} is blocked on {device} I/O.")
        io_time = random.uniform(1,
                                 5)  # Simulate different I/O burst times, I want this to be different based on type of device.
        completion_time = time.time() + io_time
        removed_process = self.remove_process()
        # And then put it in again when
        # I am just using the event loop as my loop in the simulation, I do not need queues for this.
        heapq.heappushpop(self.io_wait_queues[device], (completion_time, process))
        asyncio.create_task(self.unblock_after(io_time, removed_process))
        return

    async def block_on_sleep(self, process, sleep_time):
        # TODO: Missing the block
        """Moves a process to the sleep queue."""
        wake_time = time.time() + sleep_time
        heapq.heappushpop(self.sleep_queue, (wake_time, process))
        print(f"Process {process.pid} is now sleeping for {sleep_time:.2f} seconds.")
        removed_process = self.remove_process()
        asyncio.create_task(self.unblock_after(sleep_time, removed_process))
        return

    async def unblock_after(self, delay, process):
        await asyncio.sleep(delay)
        self.add_process(process)
        print(f"Process {process.pid} moved to READY queue.")
