import multiprocessing

import torch
import threading
import time
from schedsimulator.RRscheduler import RRScheduler
from schedsimulator.eevdf_first_sched import EEVDFScheduler


roundrobin = False

if __name__ == '__main__':

    if roundrobin:
        scheduler = RRScheduler()
        #scheduler.setup_hardware_process()
        scheduler.make_sim_RR(10)

    else:



        num_tasks = 20
        #num_latency = 13
        #num_io = 4
        #num_cpu = 3
        base_slice = 30 # Just used for the print, nothing else
        num_runs = 1   # Here you pick how many times you want to run, 10 was used in the tests.


        preemption_results = []
        throughput_results = []
        latency_results = []
        io_latency_results = []
        cpu_latency_results = []
        resp_latency_results = []
        cpu_throughput_results = []

        for i in range(num_runs):
            print(f"\n--- Run {i + 1} ---")
            seed = 42 + i
            eevdf_scheduler = EEVDFScheduler()
            (
                preemptions,
                throughput,
                avg_latency,
                avg_io_latency,
                avg_cpu_latency,
                avg_resp_latency,
                cpu_throughput
            ) = eevdf_scheduler.make_sim_eevdf(seed=seed)

            preemption_results.append(preemptions)
            throughput_results.append(throughput)
            latency_results.append(avg_latency)
            io_latency_results.append(avg_io_latency)
            cpu_latency_results.append(avg_cpu_latency)
            resp_latency_results.append(avg_resp_latency)
            cpu_throughput_results.append(cpu_throughput)


        # Compute averages
        avg_preemptions = sum(preemption_results) / num_runs
        avg_throughput = sum(throughput_results) / num_runs
        avg_latency = sum(latency_results) / num_runs
        avg_io_latency = sum(io_latency_results) / num_runs
        avg_cpu_latency = sum(cpu_latency_results) / num_runs
        avg_resp_latency = sum(resp_latency_results) / num_runs
        avg_cpu_throughput = sum(cpu_throughput_results) / num_runs


        # Print summary
        print("\n=== Summary ===")
        print(f"Num tasks: {num_tasks}")
        print(f"Base Slice: {base_slice}")
        print(f"Average preemptions: {avg_preemptions:.2f}")
        print(f"Average throughput: {avg_throughput:.7f} tasks/sec")
        print(f"Average latency (overall): {avg_latency / 1_000_000:.3f} ms")
        print(f"Average latency (interactive): {avg_resp_latency / 1_000_000:.3f} ms")
        print(f"Average latency (CPU-heavy): {avg_cpu_latency / 1_000_000:.3f} ms")
        print(f"Average latency (I/O): {avg_io_latency / 1_000_000:.3f} ms")
        print(f"Average CPU-heavy throughput: {avg_cpu_throughput:.7f} tasks/sec")




# async def main():
#     round_robin = RoundRobin(3)  # Initialize with 100 processes
#     round_robin.add_process(MathProcess(4))
#     await round_robin.scheduler() # Starts scheduling
#
# if __name__ == "__main__":
#     asyncio.run(main())  # Properly starts the event loop

# round_robin = RoundRobinGreenlet(2)  # Initialize with 100 processes
# round_robin.add_process(LockProcess(11, 13))
# round_robin.add_process(LockProcess(12, 17))
# round_robin.scheduler() # Starts scheduling


# RT_scheduler = RTScheduler()
# RT_scheduler.make_sim_FIFO(5)

# counter = 0
#
# def handler(signum, frame):
#     global counter
#     counter += 1
#     print(f"TICK {counter}")
#
# signal.signal(signal.SIGALRM, handler)
# signal.setitimer(signal.ITIMER_REAL, 0.1, 0.1)

# x = torch.randn(10000, 10000)
# for _ in range(10):
#     y = x @ x  # Long matrix multiply in native C/CUDA


# for _ in range(10):
#     for i in range(10**7):
#         pass



# counter = 0
# running = True
#
# def tick():
#     global counter
#     while running:
#         counter += 1
#         print(f"TICK {counter}")
#         time.sleep(0.1)  # 100ms
#
# # Start the ticking thread
# tick_thread = threading.Thread(target=tick, daemon=True)
# tick_thread.start()
#
# # Heavy computation in main thread
# timer.start()
# x = torch.randn(10000, 10000)
# for _ in range(10):
#     y = x @ x
#
# running = False  # Stop the ticking thread gracefully
# tick_thread.join(timeout=1)





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





