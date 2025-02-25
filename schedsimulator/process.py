import random
import time

from schedsimulator.structures.process_status import PCBStatus


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
                        # This is going block it and put it in the correct I/O queue.
                        # This will also tell a background thread to send an interrupt after a realistic random I/O time has occured.
                        device = random.choice(["disk", "network", "usb"])
                        print(f"Process {self.pid} requesting {device} I/O.")
                        scheduler.block_on_io(self, device)
                    case "Sleep":
                        print("SLEEP BLOCK")
                        # process_sleep_request(scheduler)
                        # process_io_request(scheduler)
                        # This is going block it and put it in the sleep min-queue.
                        # This will also tell a background thread to send an interrupt after a realistic random I/O time has occured.
                        sleep_time = random.uniform(1, 5)  # Random sleep time
                        print(f"Process {self.pid} sleeping for {sleep_time:.2f} seconds.")
                        scheduler.block_on_sleep(self, sleep_time)
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