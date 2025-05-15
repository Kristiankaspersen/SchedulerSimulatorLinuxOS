import asyncio
import blessed
import random
import itertools
import heapq

# Initialize blessed terminal
term = blessed.Terminal()

# Global state
READY_QUEUE = []
RUNNING_PROCESS = None
TIME_QUANTUM = 0.5  # 500ms quantum
PROCESS_COUNTER = itertools.count()
LOGS = []
LOCK = asyncio.Lock()  # Shared lock for cooperative tasks

# Process class using generators
class Process:
    def __init__(self, pid, execution_time, process_type="CPU", shared_data=None):
        self.pid = pid
        self.execution_time = execution_time
        self.remaining_time = execution_time
        self.process_type = process_type  # "CPU", "I/O", "SUM"
        self.generator = self.run()
        self.next_run_time = 0
        self.queue_order = next(PROCESS_COUNTER)
        self.shared_data = shared_data  # Shared object for cooperative work
        self.state = "Ready"

    def __lt__(self, other):
        return self.next_run_time < other.next_run_time

    def run(self):
        while self.remaining_time > 0:
            self.state = "Running"
            yield
            self.remaining_time -= TIME_QUANTUM
            self.state = "Ready"
        self.state = "Completed"

# Add new processes
def add_process(execution_time, process_type="CPU", shared_data=None):
    pid = next(PROCESS_COUNTER)
    process = Process(pid, execution_time, process_type, shared_data)
    heapq.heappush(READY_QUEUE, (process.next_run_time, process.queue_order, process))
    LOGS.append(f"Process {pid} ({process_type}) added")

# Cooperative sum task using locks
async def cooperative_sum():
    global LOCK
    shared_data = {"sum": 0}
    add_process(0.5, "SUM", shared_data)
    add_process(0.5, "SUM", shared_data)

# Async function to preempt running process
async def preempt():
    global RUNNING_PROCESS
    while True:
        await asyncio.sleep(TIME_QUANTUM)
        if RUNNING_PROCESS:
            heapq.heappush(READY_QUEUE, (RUNNING_PROCESS.next_run_time, RUNNING_PROCESS.queue_order, RUNNING_PROCESS))
            RUNNING_PROCESS = None

# Scheduler loop
async def scheduler():
    global RUNNING_PROCESS
    while True:
        if not READY_QUEUE:
            await asyncio.sleep(0.01)
            continue
        _, _, RUNNING_PROCESS = heapq.heappop(READY_QUEUE)
        try:
            next(RUNNING_PROCESS.generator)
            RUNNING_PROCESS.next_run_time += TIME_QUANTUM
            heapq.heappush(READY_QUEUE, (RUNNING_PROCESS.next_run_time, RUNNING_PROCESS.queue_order, RUNNING_PROCESS))
        except StopIteration:
            LOGS.append(f"Process {RUNNING_PROCESS.pid} completed")
            RUNNING_PROCESS = None
        await asyncio.sleep(0.01)

# User Input Handling with blessed
async def user_input():
    with term.cbreak(), term.hidden_cursor():
        while True:
            inp = term.inkey(timeout=0.1)
            if inp.lower() == 'c':
                add_process(random.uniform(0.3, 1.0), "CPU")
            elif inp.lower() == 'i':
                add_process(random.uniform(0.3, 1.0), "I/O")
            elif inp.lower() == 's':
                await cooperative_sum()
            elif inp.lower() == 'q':
                break
            await asyncio.sleep(0.1)

# Blessed UI loop
async def ui():
    while True:
        with term.location(0, 0):
            print(term.clear)
            print(term.bold_white_on_black("=== Process Scheduler ==="))
            print(term.green(f"Running: {RUNNING_PROCESS.pid if RUNNING_PROCESS else 'None'}"))
            print(term.yellow(f"Ready Queue: {', '.join(str(p.pid) for _, _, p in READY_QUEUE) if READY_QUEUE else 'Empty'}"))
            print(term.cyan(f"Logs:"))
            for log in LOGS[-5:]:
                print(term.white(f" - {log}"))
            print(term.magenta("\nPress C (CPU Task), I (I/O Task), S (Sum Task), Q (Quit)"))
        await asyncio.sleep(0.1)

# Run everything
async def main():
    await asyncio.gather(preempt(), scheduler(), user_input(), ui())

asyncio.run(main())
