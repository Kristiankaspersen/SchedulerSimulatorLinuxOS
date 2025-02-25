import heapq
import threading
import time


import heapq
import threading
import time
import random

class EventManager:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.sleep_queue = []  # Min-heap for sleeping processes (wake_time, process)
        self.io_wait_queues = {  # Track when I/O should be completed
            "disk": [],
            "network": [],
            "usb": [],
        }
        self.completed_events = []
        self.lock = threading.Lock()
        self.event_thread = threading.Thread(target=self.run, daemon=True)
        self.running = True

    def start(self):
        """Starts the event manager thread."""
        self.event_thread.start()

    def add_sleep_event(self, wake_time, process):
        """Adds a sleeping process to the event queue."""
        with self.lock:
            heapq.heappush(self.sleep_queue, (wake_time, process))

    def add_io_event(self, process, device, io_time):
        """Adds a process to the I/O queue and sets an interrupt timer."""
        wake_time = time.time() + io_time
        with self.lock:
            heapq.heappush(self.io_wait_queues[device], (wake_time, process))

    def run(self):
        """Background thread that handles wake-up events (interrupt simulation)."""
        while self.running:
            with self.lock:
                current_time = time.time()

                # Handle sleep wake-ups
                while self.sleep_queue and self.sleep_queue[0][0] <= current_time:
                    _, process = heapq.heappop(self.sleep_queue)
                    print(f"EventManager: Process {process.pid} woke up from sleep.")
                    self.completed_events.append(process)

                # Handle I/O completion for each device
                for device in self.io_wait_queues:
                    while self.io_wait_queues[device] and self.io_wait_queues[device][0][0] <= current_time:
                        _, process = heapq.heappop(self.io_wait_queues[device])
                        print(f"EventManager: Process {process.pid} completed {device} I/O.")
                        self.completed_events.append(process)

            time.sleep(0.1)  # Avoid busy-waiting

    def get_completed_events(self):
        """Returns all processes that are ready to be scheduled again."""
        with self.lock:
            completed = self.completed_events[:]
            self.completed_events.clear()
            return completed

    def stop(self):
        """Stops the event loop."""
        self.running = False
        self.event_thread.join()
