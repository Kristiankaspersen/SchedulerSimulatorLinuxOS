# 100ms time slice, shift this to shift the preemption time.
# Used in signal
import itertools

INIT_TREE = True
initial_deadline_diff = 0
initial_vr_diff = 0



TICK_SEC = 0.01 # 1 ms
#TICK_NSEC = 10_000_000 # 1 ms
#sysctl_sched_base_slice = 100_000_000   # 28ms slice, in nanoseconds (Linux uses ns internally)

# TEST
TICK_NSEC = 1 # 1 ms
sysctl_sched_base_slice = 30   # 28ms slice, in nanoseconds (Linux uses ns internally)

NICE_0_LOAD = 1024 # baseline weight for nice=0
PLACE_LAG = True # Begin with this lag thing ON.
RUN_TO_PARITY = True # Begin with this ON.
PREEMPT_SHORT = True # Begin with this ON.
SLEEP_TIME_INTERACTIVE = 3
SLEEP_TIME_IO = 10

#TASKS
NUM_INTERACTIVE = 12
NUM_CPU = 4
NUM_IO = 4
# TOT: 20 tasks

# FOR Q-LEARNER
ADAPTIVE = False # Set the adaptive version to true of false.
cpu_offset = 0
interactive_offset = 0
EXIT_COUNT = 20
INTERACTIVE_TIME_WINDOW = 100
# This is new for counting the negative lag accumulated. (for debugging)
io_negative_count = 0
interactive_negative_count = 0

nice_to_weight = {
        -20: 88761, -19: 71755, -18: 56483, -17: 46273, -16: 36291,
        -15: 29154, -14: 23254, -13: 18705, -12: 14949, -11: 11916,
        -10: 9548, -9: 7620, -8: 6100, -7: 4904, -6: 3906,
        -5: 3121, -4: 2501, -3: 1991, -2: 1586, -1: 1277,
        0: 1024, 1: 820, 2: 655, 3: 526, 4: 423,
        5: 335, 6: 272, 7: 215, 8: 172, 9: 137,
        10: 110, 11: 87, 12: 70, 13: 56, 14: 45,
        15: 36, 16: 29, 17: 23, 18: 18, 19: 15
    }

