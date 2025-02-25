import heapq
import random
import time

from schedsimulator.dispatcher import Dispatcher
from schedsimulator.event_manager import EventManager
from schedsimulator.process import Process
from schedsimulator.structures.linked_queue import TheQueue
from schedsimulator.structures.process_status import PCBStatus


class RoundRobin:
    def __init__(self, num_processes):
        # Inits a roundrobin queue with num_processes.
        self.io_wait_queues = {  # Separate queues for each I/O device
            "disk": TheQueue(),
            "network": TheQueue(),
            "usb": TheQueue(),
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
        self.dispatcher = Dispatcher(self.current_process)

        self.event_manager = EventManager(self)
        self.event_manager.start()  # Start event manager thread

        # So I think I will simulate it here, and a new thread can be made.

    def scheduler(self):
        if self.current_process is not None:
            self.check_unblocked_processes()
            match self.current_process.status:
                case PCBStatus.NEW:
                    print("STATUS NEW, sched")
                    self.current_process = self.current_process.next
                case PCBStatus.READY:
                    print("STATUS READY, sched, preempt")
                    self.current_process = self.current_process.next
                case PCBStatus.EXIT:
                    print("STATUS EXIT, sched")
                    self.processes_in_ready_queue -= 1
                    self.remove_process()
                case PCBStatus.BLOCKED:
                    print("STATUS BLOCKED sched")
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
                self.dispatcher.dispatch(self)
            else:
                # So this will always happen when exit is called, since then the last one is removed.
                # So now the program just stops when there are no more threads left, is this what I want? Or a halt?
                # But then again how am I supposed to measure.
                print("The READY queue is empty 2")
        else:
            print("The READY queue is empty 1")
            # Wait for new processes to start running again.

    def exit(self):
        self.current_process.status = PCBStatus.EXIT
        self.scheduler()

    def yields(self):
        # Just do next process
        # Run scheduler with PCB status ready
        self.current_process.status = PCBStatus.READY
        self.scheduler()

    def block(self, blockedQueue):
        # Put current process in blocked queue
        # Remove from ready queue and put inside the blocked queue.
        # This is wrong. ......................
        self.remove_process()
        blockedQueue.push(self.current_process)
        self.scheduler()

    # def block_io(self, device):
    #     """Moves a process to the I/O wait queue and assigns a completion time"""
    #     io_time = time.time() + get_io_latency(device)  # Compute when I/O will complete
    #     self.remove_process()
    #     # TODO Not sure if I can use my queue here (check this one out)
    #     self.io_wait_queues[device].push((self.current_process, io_time))
    #     print(f"Process {self.current_process.pid} waiting for {device} I/O until {io_time:.2f}")
    #
    # def block_sleep(self, duration):
    #     """Moves a process to the sleep queue with a wake-up time"""
    #     wake_time = time.time() + duration
    #     print(f"Process {self.current_process.pid} sleeping for {duration} seconds (wakes up at {wake_time:.2f})")
    #     heapq.heappush(self.sleep_queue, (wake_time, self.current_process))

    def unblock(self, blocked_queue):
        # Unblock first process in blocked queue
        self.add_process(blocked_queue.pop())

    def unblock2(self, process):
        # Unblock first process in blocked queue
        self.add_process(process)
        print(f"Process {process.pid} moved to READY queue.")

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

    def check_unblocked_processes(self):
        """Moves unblocked processes to the ready queue."""
        completed_processes = self.event_manager.get_completed_events()
        for process in completed_processes:
            print(f"Scheduler: Moving process {process.pid} to ready queue.")
            self.add_process(process)

    def block_on_io(self, process, device):
        """Moves a process to the I/O queue and starts an I/O interrupt timer."""
        print(f"Process {process.pid} is blocked on {device} I/O.")
        self.io_wait_queues[device].push(process)
        io_time = random.uniform(1, 5)  # Simulate different I/O burst times, I want this to be different based on type of device.
        self.event_manager.add_io_event(process, device, io_time)

    def block_on_sleep(self, process, sleep_time):
        """Moves a process to the sleep queue."""
        wake_time = time.time() + sleep_time
        heapq.heappushpop(self.sleep_queue, (wake_time, process))
        print(f"Process {process.pid} is now sleeping for {sleep_time:.2f} seconds.")
        self.event_manager.add_sleep_event(wake_time, process)

