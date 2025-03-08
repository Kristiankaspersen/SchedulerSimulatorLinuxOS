import greenlet
from schedsimulator.structures.process_status import PCBStatus
import random
class GreenletProc:
    def __init__(self, pid):
        self.pid = pid
        #self.greenlet = greenlet.greenlet(self.run)  # Create a greenlet for this process
        self.green = greenlet.greenlet(self.run)  # Pass self as an argument
        self.next = None  # Next process in round-robin scheduling
        self.status = PCBStatus.NEW
        self.cpu_work = random.randint(100, 1000000)
        self.cpu_work = 100
        self.other_number = self.cpu_work // 10
        self.other_number = 10
    #
    def run(self, scheduler):
        """Simulated CPU-bound task that gets preempted."""
        print(f"▶️ Process {self.pid} started.")
        for i in range(self.cpu_work):  # Simulating CPU work
            if i % self.other_number == 0:
                print(f"Process {self.pid} at step {i}")
            #greenlet.getcurrent().parent.switch()  # Voluntarily switch (will be overridden by SIGALRM)

        print(f" Process {self.pid} finished execution.")

        scheduler.exit()

# class GreenletProc(greenlet.greenlet):  # ✅ Subclass greenlet
#     def __init__(self, pid):
#         super().__init__()  # ✅ Initialize greenlet properly
#         self.pid = pid
#         self.next = None
#         self.status = PCBStatus.NEW
#         self.cpu_work = 1000
#         self.other_number = 100
#
#     def run(self):  # ✅ This will now execute when switch() is called
#         print(f"▶️ Process {self.pid} started running!")
#         for i in range(self.cpu_work):
#             if i % self.other_number == 0:
#                 print(f"Process {self.pid} at step {i}")
#             greenlet.getcurrent().parent.switch()  # ✅ Preempt back to scheduler
#         print(f"✅ Process {self.pid} finished execution.")