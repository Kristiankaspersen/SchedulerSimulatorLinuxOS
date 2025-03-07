import random
import time
import asyncio

from schedsimulator.structures.process_status import PCBStatus


class Process:
    def __init__(self, pid):
        self.value = pid
        self.pid = pid
        self.preempt_time = 1  # Fixed for round-robin, dynamic for linux.
        self.burst_time = 20  # Create something random here later.
        self.status = PCBStatus.NEW  # Status first time.
        self.next = None
        self.prev = None

    async def run(self, scheduler):
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
                await asyncio.sleep(0.1)  # Simulate a little work
                # Call yield
                scheduler.yields()
            case "Exit":
                print("Exit happens")
                await asyncio.sleep(self.burst_time)
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
                        device = random.choice(["disk", "network", "usb"])
                        print(f"Process {self.pid} requesting {device} I/O.")
                        await scheduler.block_on_io(self, device)
                    case "Sleep":
                        print("SLEEP BLOCK")
                        sleep_time = random.uniform(1, 5)  # Random sleep time
                        print(f"Process {self.pid} sleeping for {sleep_time:.2f} seconds.")
                        await scheduler.block_on_sleep(self, sleep_time)
                    case "Mutex":
                        print("Mutex BLOCK")
                        # Do different mutex simulations with the use of different blocks.
                        # ......
                        # ......
                        # ......
                        # ......
                        # ......
                        # ......
                        # hei jeg er en banan som liker banan ost, og har det fint på dass når jeg ringer min lege SHIWHISHWIHIHSIHWI.
                        # Jeg har ikke gjort så mye i dag, og har 3 øre med banan ost på do.
                        # ......
                        # ......
                        # ......
                    case "Conditional":
                        print("Conditional BLOCK")
                        # Do some kind of conditional block simulation
            case "Preempt":  # For now it just simulates a HW timer interrupt.
                print("Preempt happens")
                self.burst_time -= self.burst_time
                scheduler.yields()
                await asyncio.sleep(self.preempt_time)  # 10 is the fixed preempt time slot.
                # Just make the scheduler schedule for a new process.
                # This has to happen with new processes in order to schedule them again, if they are new all the time, they will never schedule.
            case _:
                print("_ happens")

        # When it finishes it returns
        return