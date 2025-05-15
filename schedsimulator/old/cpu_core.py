

class CPU:
    def __init__(self, cpu_id):
        self.id = cpu_id
        self.rt_queues = {priority: deque() for priority in range(100)}  # 100 FIFO queues for RT
        self.sched_other_tree = []  # This will be a min-heap for SCHED_OTHER tasks
        self.current_task = None

    def tick(self):
        # Handle RT tasks (FIFO or RR)
        for priority in range(100):
            if self.rt_queues[priority]:
                self.current_task = self.rt_queues[priority].popleft()
                print(f"CPU {self.id} running RT task {self.current_task.pid} with priority {priority}")
                self.current_task.tick()
                if self.current_task.remaining_time <= 0:
                    print(f"CPU {self.id} finished RT task {self.current_task.pid}")
                    self.current_task = None
                break  # FIFO, so once we pick a task, we run it till it's finished.

        # Handle non-RT tasks (SCHED_OTHER, BATCH, IDLE using red-black tree)
        if not self.current_task and self.sched_other_tree:
            self.current_task = heapq.heappop(self.sched_other_tree)  # Min-heap simulates red-black tree for simplicity
            print(f"CPU {self.id} running SCHED_OTHER task {self.current_task.pid}")
            self.current_task.tick()

            if self.current_task.remaining_time <= 0:
                print(f"CPU {self.id} finished SCHED_OTHER task {self.current_task.pid}")
                self.current_task = None

    def add_task(self, task):
        if task.policy in ['FIFO', 'RR']:  # RT tasks
            self.rt_queues[task.priority].append(task)
        elif task.policy == 'SCHED_OTHER':
            heapq.heappush(self.sched_other_tree, (task.priority, task))  # Using priority for SCHED_OTHER
        # Other policies can be added similarly

    def is_idle(self):
        return not self.current_task and not any(self.rt_queues.values()) and not self.sched_other_tree


def load_balance(cpus):
    # Simple work stealing (pulling tasks from busy CPUs)
    for cpu in cpus:
        if cpu.is_idle():
            donor = max(cpus, key=lambda c: len(c.rt_queues[99]) + len(c.sched_other_tree))
            if donor != cpu:
                # Steal a task from donor
                if donor.rt_queues[99]:
                    stolen_task = donor.rt_queues[99].pop()
                    cpu.add_task(stolen_task)
                    print(f"CPU {cpu.id} stole RT task {stolen_task.pid} from CPU {donor.id}")
                elif donor.sched_other_tree:
                    stolen_task = heapq.heappop(donor.sched_other_tree)[1]
                    cpu.add_task(stolen_task)
                    print(f"CPU {cpu.id} stole SCHED_OTHER task {stolen_task.pid} from CPU {donor.id}")