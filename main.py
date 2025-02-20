# Conclusion, I have one scheduler per CPU. Then this will work.
# They do that in Linux,
# I will simplyfy here without parent processeses etc. All processes will have the same level. And when exited, it just exits.

from enum import Enum
import time
import random
import heapq


# TODO Make a PCB status for linux as well.
# TODO MAke the data for the process simular to linux.
class PCBStatus(Enum):
    NEW = 0
    READY = 1
    EXIT = 2
    BLOCKED = 3


current_process = None


def io_unblock_task(scheduler):
    """System process that checks I/O queues and unblocks processes when their I/O is done"""
    print("Does this even happen??? IN IO UNBLOCK NOW")
    current_time = time.time()
    for device, queue in scheduler.io_wait_queues.items():
        to_unblock = []
        for process, completion_time in queue:
            if current_time >= completion_time:  # I/O is done
                to_unblock.append(process)

        # TODO: look for optimisation here.
        # Remove completed I/O processes from the queue
        scheduler.io_wait_queues[device] = [(p, t) for p, t in queue if p not in to_unblock]

        # Move completed processes back to READY queue
        for process in to_unblock:
            print(f"{device} I/O completed for process {process.pid}, unblocking.")
            scheduler.unblock2(process)


def sleep_unblock_task(scheduler):
    """System process that checks sleeping processes and wakes them up when time expires"""

    print("Does this even happen??? IN SLEEP UNBLOCK NOW")
    current_time = time.time()

    if scheduler.sleep_queue is None:
        print("HEEEEEEY")

    # Wake up processes in order
    while scheduler.sleep_queue and scheduler.sleep_queue[0][0] <= current_time:
        wake_time, process = heapq.heappop(scheduler.sleep_queue)  # O(log n) removal
        print(f"Process {process.pid} woke up from sleep.")
        scheduler.unblock2(process)


def process_io_request(scheduler):
    """Simulates a process making an I/O request"""
    device = random.choice(["disk", "network", "usb"])  # Random I/O device
    scheduler.block_io(device)


def process_sleep_request(scheduler):
    """Simulates a process making a sleep request"""
    sleep_duration = random.uniform(1, 5)  # Random sleep time
    """Put a process to sleep."""
    scheduler.block_sleep(sleep_duration)


def get_io_latency(device):
    """Simulates different I/O speeds per device"""
    latencies = {
        "disk": random.uniform(2, 5),  # Disk I/O is slow
        "network": random.uniform(0.5, 2),  # Network I/O is faster
        "usb": random.uniform(1, 3),
    }
    return latencies[device]

class Process:
    def __init__(self, pid):
        self.pid = pid
        self.preempt_time = 10  # Fixed for round-robin, dynamic for linux.
        self.burst_time = 12  # Create something random here later.
        self.status = PCBStatus.NEW  # Status first time.
        self.next = None  # Next
        self.prev = None  # Trenger ikke denne på FIFO Queue. Trenger den til RoundRobin

    def run(self, scheduler):
        """Simulates process execution"""
        # Simulate that it yields, or preempt, and how much of the process time is left.

        # What if I change these, based on some kind of probability?
        # I mean to make it more realistic, I do not think yield happens so often. And I think blocked happen way more often.
        # In this case Exit is just a normal thread, with no block or yield operation. Or a process in a state where there is no more yield or block operations to be done.
        actions = ["Yield", "Exit", "Block"]
        action = random.choice(actions)

        if action == "Exit":
            if self.burst_time >= self.preempt_time:
                action = "Preempt"

        match action:
            case "Yield":
                print("Yield happens")
                time.sleep(1)  # Simulate a little work
                # Call yield
                scheduler.yields()
            case "Exit":
                print("Exit happens")
                time.sleep(self.burst_time)
                # Call exit
                scheduler.exit()
            case "Block":
                # Make a
                # I Will wait with number 5. When w process calls wait, for a child, the parent is blocked.
                #   - I am not sure of the situations this is used in. Have to expand on this later on.
                block_actions = ["IO", "Sleep", "Conditional", "Mutex"]
                block_action = random.choice(block_actions)
                match block_action:
                    case "IO":
                        print("IO BLOCK")
                        # process_io_request(scheduler)
                    case "Sleep":
                        print("SLEEP BLOCK")
                        # process_sleep_request(scheduler)
                    case "Mutex":
                        print("Mutex BLOCK")
                        # Just schedule for now.
                        # scheduler.scheduler()
                    case "Conditional":
                        print("Conditional BLOCK")
                        # Just schedule for now.
                        # scheduler.scheduler()
                # Simulate a little work, It can be different time here based on type of block.
                # I really have to think about this one more.
                # Do some block activity
                # Each I/O device, networks etc, has its own waiting queue.
                # 1. I/O Waiting queue
                #     - Each IO device (disk, network, etc.) has its own waiting queue
                #     - When a process calls read(), it waits in the corresponding I/O wait queue until the data is available
                #     - Example: process -> waiting for disk read -> wakes up when read completes.
                # 2. Lock/Mutex Blocked queue
                #     - Each lock (mutex, semaphore, futex) maintains its own queue of blocked threads.
                #     - When a thread tries to acquire a locked mutex, it waits in the mutex's wait queue
                #     - When unlock() is called, the scheduler wakes up one (or more) blocked threads
                #     - Example: Process A holds mutex -> process B blocks -> A releases mutex -> B wakes up
                # 3. Condition variables blocked queue
                # 4. Timer based sleep queue
                #      - The kernel maintains a sleep queue for processes waiting on sleep(), nanosleep(), or usleep()
                #      - The scheduler periodically checks if the sleep time is over and moves the process to the ready queue
                #      - Example: process calls sleep(5) -> scheduler wakes it up after 5 seconds
                # I will wait wit this
                # 5. Process waiting queue
                #       - When a parent calls wait() for child, the parent is blocked in the process wait queue.
                #       - Once the child process terminates, the parent is unblocked.
                #
                # For simulation sake I can make different blockding queues that are more similar to each of these situations.
                # scheduler.block()
                # If it is blocked we need to be able to unblock it again though, come back to this problem.
                scheduler.scheduler()
            case "Preempt":  # For now it just simulates a HW timer interrupt.
                print("Preempt happens")
                self.burst_time -= self.burst_time
                time.sleep(self.preempt_time)  # 10 is the fixed preempt time slot.
                # Just make the scheduler schedule for a new process.
                scheduler.scheduler()
            case _:
                print("_ happens")
                scheduler.scheduler()


class SystemProcess(Process):
    def __init__(self, pid, system_task):
        super().__init__(pid)
        self.system_task = system_task  # Define what system task this process does

    def run(self, scheduler):
        """Runs the system process task"""
        print("THIS RUN NEVER HAPPENS")
        self.system_task(scheduler)
        scheduler.yields()  # Once done, yield to the next process


class Dispatcher:
    def __init__(self, current_process):
        # This is wrong isnt it?? Yes it is.
        self.current_process = current_process

    def dispatch(self, scheduler):
        """Runs the picked process from the scheduler"""
        #self.current_process.run(scheduler)
        scheduler.current_process.run(scheduler)


class TheQueue:
    def __init__(self):
        self.tail = None  # out first
        self.head = None  # put in

    def pop(self):
        queue_head = None
        if self.empty():
            print("Empty")
        else:
            queue_head = self.head
            if self.head == self.tail:
                self.tail = self.head.next  # In this case self.head.next would be None. Meaning both head and tail would be None.
            self.head = self.head.next
        return queue_head

    def push(self, node):
        if self.empty():
            self.tail = node
            self.head = node
        else:
            self.tail.next = node
            self.tail = self.tail.next

    def empty(self):
        return self.tail is None and self.head is None

    # Making the queue iterable
    def __iter__(self):
        self._iter_node = self.head  # Start iteration from head
        return self

    def __next__(self):
        if self._iter_node is None:
            raise StopIteration
        value = self._iter_node.value
        self._iter_node = self._iter_node.next
        return value


class RoundRobin:
    def __init__(self, num_processes):
        # Inits a roundrobin queue with num_processes.
        self.io_wait_queues = {  # Separate queues for each I/O device
            "disk": TheQueue(),
            "network": TheQueue(),
            "usb": TheQueue(),
        }
        self.sleep_queue = []  # Stores (process, wake_time) #TODO Only thing i need to do, is push to the list, with use of heapq
        process = Process(0)
        self.current_process = process
        for i in range(num_processes - 1):
            process.next = Process(i + 1)  # Next is new node
            process.next.prev = process  # New node prev is the old process
            process = process.next  # Then update the new process to be the old for the next iteration.
        # What is the last process now
        self.current_process.prev = process
        process.next = self.current_process
        # Add system processes for handling I/O and Sleep
        self.add_process(SystemProcess(num_processes, io_unblock_task))  # Handle I/O completion
        self.add_process(SystemProcess(num_processes + 1, sleep_unblock_task))  # Handle sleep wake-up
        # Now process is in the end of the queue
        # current process is the first in the queue, that is going to start.
        # Go through the queue, and check if everything is correct.
        self.processes_in_ready_queue = num_processes + 2
        current = self.current_process
        for i in range(self.processes_in_ready_queue):
            print(current.pid)
            current = current.prev
        self.dispatcher = Dispatcher(self.current_process)

        # So I think I will simulate it here, and a new thread can be made.

    def scheduler(self):
        if self.current_process is not None:
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

    def block_io(self, device):
        """Moves a process to the I/O wait queue and assigns a completion time"""
        io_time = time.time() + get_io_latency(device)  # Compute when I/O will complete
        self.remove_process()
        # TODO Not sure if I can us my queue here (check this one out)
        self.io_wait_queues[device].push((self.current_process, io_time))
        print(f"Process {self.current_process.pid} waiting for {device} I/O until {io_time:.2f}")

    def block_sleep(self, duration):
        """Moves a process to the sleep queue with a wake-up time"""
        wake_time = time.time() + duration
        print(f"Process {self.current_process.pid} sleeping for {duration} seconds (wakes up at {wake_time:.2f})")
        heapq.heappush(self.sleep_queue, (wake_time, self.current_process))

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


roundRobin = RoundRobin(1)
roundRobin.dispatcher.dispatch(roundRobin)
# First in First out linked queue structure.
# Blocked queue.


# ----------------------------
# new_queue = TheQueue()      |
# new_queue.push(Node(1))     |
# node = new_queue.pop()      |
# print(node.pid)           |
# new_queue.pop()             |
# new_queue.push(Node(2))     |
# new_queue.pop()             |
# current_process = Node(1)   |
# -----------------------------


# NOTE:
# There will be limitations on sleep and I/O, since I have no hardware interrupt that can interrupt when an I/O device is done.
# The same for sleep. I think there is a hardware interrupt in this case as well? If I am not mistaken.
