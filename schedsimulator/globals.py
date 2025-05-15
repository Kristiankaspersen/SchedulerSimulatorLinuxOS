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
PREEMPT_SHORT = False # Begin with this ON.
# FOR Q-LEARNER
ADAPTIVE = False
cpu_offset = 0
interactive_offset = 0

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

