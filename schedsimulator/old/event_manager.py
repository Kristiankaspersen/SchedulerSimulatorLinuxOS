import heapq
import threading
import time
import random

class EventManager:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.completed_events = []
        self.lock = threading.Lock()
        self.critical_section = threading.Lock()
        self.event_thread = threading.Thread(target=self.run, daemon=True)
        self.running = True

    def start(self):
        """Starts the event manager thread."""
        self.event_thread.start()


    def add_io_event(self):
        self.running = True
        self.run()

    def add_sleep_event(self):
        self.running = True
        self.run()

    def run(self):
        """Background thread that handles wake-up events (interrupt simulation)."""
        while self.running:
            # if not self.scheduler.sleep_queue and all(io_queue.empty() for io_queue in self.scheduler.io_wait_queues.values()):
            #     self.running = False

            with self.lock:
                current_time = time.time()

                # 🔹 Handle Sleep Wake-Ups
                while self.scheduler.sleep_queue and self.scheduler.sleep_queue[0][0] <= current_time:
                    _, process = heapq.heappop(self.scheduler.sleep_queue)
                    print(f"EventManager: Process {process.pid} woke up from sleep.")
                    self.scheduler.add_process(process)

                # 🔹 Handle I/O Completion for Each Device
                for device, io_queue in self.scheduler.io_wait_queues.items():
                    while io_queue and io_queue[0][0] <= current_time:
                        _, process = heapq.heappop(io_queue)
                        print(f"EventManager: Process {process.pid} completed {device} I/O.")
                        self.scheduler.add_process(process)

            time.sleep(0.1)  # Avoid busy-waiting

    # Maybe later in my simulation I will try to use actual interrupts.
    def handle_interrupt(self, process):
        """Handles an interrupt by pausing the scheduler, processing the event, and resuming."""
        print("EventManager: INTERRUPT TRIGGERED! Waiting for critical section...")

        with self.critical_section:
            print("EventManager: Now handling interrupt.")
            self.completed_events.append(process)

        # 🔹 Resume Scheduler Execution After Handling Interrupt
        self.scheduler.pause_event.set()
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
