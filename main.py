
from schedsimulator.round_robin import RoundRobin


roundRobin = RoundRobin(1)
roundRobin.dispatcher.dispatch(roundRobin)

# NOTES:
# - I will use a thread to simulate HW interrupts that will run in the background. For now this will be done for I/O and Sleep blocks in the scheduler.
#    - So for I/O there will be different block queues for disk, usb, network etc.
#    - For Sleep there will be a min-max queue
#    -


# def io_unblock_task(scheduler):
#     """System process that checks I/O queues and unblocks processes when their I/O is done"""
#     print("Does this even happen??? IN IO UNBLOCK NOW")
#     current_time = time.time()
#     for device, queue in scheduler.io_wait_queues.items():
#         to_unblock = []
#         for process, completion_time in queue:
#             if current_time >= completion_time:  # I/O is done
#                 to_unblock.append(process)
#
#         # TODO: look for optimisation here.
#         # Remove completed I/O processes from the queue
#         scheduler.io_wait_queues[device] = [(p, t) for p, t in queue if p not in to_unblock]
#
#         # Move completed processes back to READY queue
#         for process in to_unblock:
#             print(f"{device} I/O completed for process {process.pid}, unblocking.")
#             scheduler.unblock2(process)
#
#
# def sleep_unblock_task(scheduler):
#     """System process that checks sleeping processes and wakes them up when time expires"""
#
#     print("Does this even happen??? IN SLEEP UNBLOCK NOW")
#     current_time = time.time()
#
#     if scheduler.sleep_queue is None:
#         print("HEEEEEEY")
#
#     # Wake up processes in order
#     while scheduler.sleep_queue and scheduler.sleep_queue[0][0] <= current_time:
#         wake_time, process = heapq.heappop(scheduler.sleep_queue)  # O(log n) removal
#         print(f"Process {process.pid} woke up from sleep.")
#         scheduler.unblock2(process)
#
#
# def process_io_request(scheduler):
#     """Simulates a process making an I/O request"""
#     device = random.choice(["disk", "network", "usb"])  # Random I/O device
#     scheduler.block_io(device)
#
#
# def process_sleep_request(scheduler):
#     """Simulates a process making a sleep request"""
#     sleep_duration = random.uniform(1, 5)  # Random sleep time
#     """Put a process to sleep."""
#     scheduler.block_sleep(sleep_duration)


# def get_io_latency(device):
#     """Simulates different I/O speeds per device"""
#     latencies = {
#         "disk": random.uniform(2, 5),  # Disk I/O is slow
#         "network": random.uniform(0.5, 2),  # Network I/O is faster
#         "usb": random.uniform(1, 3),
#     }
#     return latencies[device]





