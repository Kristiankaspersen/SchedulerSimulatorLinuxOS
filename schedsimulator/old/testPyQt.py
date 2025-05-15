import time

from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, \
    QWidget, QTextEdit
import sys
import asyncio
import random
import itertools
import heapq
from qasync import QEventLoop, asyncSlot

# Global state
READY_QUEUE = []
RUNNING_PROCESS = None
TIME_QUANTUM = 0.5  # 500ms quantum
PROCESS_COUNTER = itertools.count()
LOGS = []


class Process:
    def __init__(self, pid, execution_time, process_type="CPU"):
        self.pid = pid
        self.execution_time = execution_time
        self.remaining_time = execution_time
        self.process_type = process_type  # "CPU" or "I/O"
        self.generator = self.run()
        self.next_run_time = 0
        self.queue_order = next(PROCESS_COUNTER)
        self.state = "Ready"

    def __lt__(self, other):
        return self.next_run_time < other.next_run_time

    def run(self):
        while self.remaining_time > 0:
            self.state = "Running"
            asyncio.sleep(10)
            yield
            self.remaining_time -= TIME_QUANTUM
            self.state = "Ready"
        self.state = "Completed"


# Add new processes
def add_process(execution_time, process_type="CPU"):
    pid = next(PROCESS_COUNTER)
    process = Process(pid, execution_time, process_type)
    heapq.heappush(READY_QUEUE, (process.next_run_time, process.queue_order, process))
    LOGS.append(f"Process {pid} ({process_type}) added")


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


class SchedulerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Scheduler")
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout()

        # Process Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["PID", "State", "Type"])
        self.layout.addWidget(self.table)

        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.layout.addWidget(self.log_output)

        # Buttons
        self.cpu_button = QPushButton("Add CPU Task")
        self.cpu_button.clicked.connect(lambda: add_process(random.uniform(0.3, 1.0), "CPU"))
        self.layout.addWidget(self.cpu_button)

        self.io_button = QPushButton("Add I/O Task")
        self.io_button.clicked.connect(lambda: add_process(random.uniform(0.3, 1.0), "I/O"))
        self.layout.addWidget(self.io_button)

        # Main Widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        # Start UI update loop
        self.update_ui()

    @asyncSlot()
    async def update_ui(self):
        """ Updates the UI to reflect the scheduler state """
        self.table.setRowCount(len(READY_QUEUE) + (1 if RUNNING_PROCESS else 0))
        row = 0

        # Running process
        if RUNNING_PROCESS:
            self.table.setItem(row, 0, QTableWidgetItem(str(RUNNING_PROCESS.pid)))
            self.table.setItem(row, 1, QTableWidgetItem("Running"))
            self.table.setItem(row, 2, QTableWidgetItem(RUNNING_PROCESS.process_type))
            row += 1

        # Ready queue
        for _, _, process in READY_QUEUE:
            self.table.setItem(row, 0, QTableWidgetItem(str(process.pid)))
            self.table.setItem(row, 1, QTableWidgetItem(process.state))
            self.table.setItem(row, 2, QTableWidgetItem(process.process_type))
            row += 1

        # Update log output
        self.log_output.setPlainText("\n".join(LOGS[-5:]))

        # Schedule next update
        await asyncio.sleep(0.5)
        await self.update_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = SchedulerGUI()
    window.show()

    with loop:
        loop.run_until_complete(asyncio.gather(preempt(), scheduler(), window.update_ui()))
