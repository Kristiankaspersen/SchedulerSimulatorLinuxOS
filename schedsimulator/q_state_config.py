# Define possible states (state as a tuple: (interactive_bucket, cpu_bound_bucket, responsiveness_bucket, throughput_bucket))
import itertools
from schedsimulator.enums.actions import Action

interactive_buckets = [0, 1, 2, 3, 4]  # Idle, Very few, Moderate, Many, Burst
cpu_bound_buckets = [0, 1]              # 0 (none) or 1 (one or more CPU-heavy)
responsiveness_buckets = [0, 1, 2, 3]       # Low, Moderate, High, Very High
throughput_buckets = [0, 1, 2, 3]        # Low, Moderate, High, Very High

states = list(itertools.product(
    interactive_buckets,
    cpu_bound_buckets,
    responsiveness_buckets,
    throughput_buckets
))

actions = [
    Action.INCREASE_INTERACTIVE,
    Action.DECREASE_INTERACTIVE,
    Action.INCREASE_CPU,
    Action.DECREASE_CPU,
    Action.RESET_ALL,
    Action.PRIORITIZE_INTERACTIVE
]
