import random
import itertools
from collections import defaultdict
from pprint import pprint
from schedsimulator.q_state_config import states, actions
from schedsimulator.enums.process_status import TaskStatus
from schedsimulator.enums.task_type import TaskType
from schedsimulator.enums.actions import Action
from schedsimulator.globals import sysctl_sched_base_slice
import schedsimulator.globals as globals


learning_log = []  # Stores (state, action, reward, next_state, cpu_offset)

NUM_STATES = 160
NUM_ACTIONS = 6

alpha = 0.05        # Learning rate
gamma = 0.9       # Discount factor
epsilon = 0.0  #  Exploration probability

last_state = (2, 1, 2, 1)   # Moderate interactivity, CPU-heavy present, moderate latency/preempt
last_action = 2  # "reset_slice" (index 2) is neutral

WEIGHT_TABLE = {
    0: (0.1, 0.9),  # No interactivity
    1: (0.4, 0.6),  # Very few interactive
    2: (0.5, 0.5),  # Moderate
    3: (0.7, 0.3),  # Many
    4: (0.9, 0.1)   # Burst
}
episodes = 0

# Initialize empty Q-table
Q = defaultdict(lambda: {a: 0.0 for a in actions})

def is_high_interactivity(state):
    interactivity = state[0]
    return interactivity >= 3  # bucket 3 or 4

def is_moderate_interactivity(state):
    interactivity = state[0]
    return interactivity == 2  # bucket 3 or 4

def is_cpu_heavy(state):
    cpu_bound = state[1]
    return cpu_bound == 1  # 1 = one or more CPU-bound tasks

def seed_q_table():
    Q = defaultdict(lambda: {a: 0.0 for a in actions})

    for state in states:
        for action in actions:
            Q[state][action] = 0.0  # Default

            if is_high_interactivity(state):
                if action == Action.PRIORITIZE_INTERACTIVE:
                    Q[state][action] = +1
                elif action == Action.INCREASE_INTERACTIVE:
                    Q[state][action] = -0.05
                elif action == Action.DECREASE_INTERACTIVE:
                    Q[state][action] = +0.1  # Boost this one in high interactivity

            elif is_moderate_interactivity(state):
                if action == Action.RESET_ALL:
                    Q[state][action] = +0.1
                elif action == Action.DECREASE_INTERACTIVE:
                    Q[state][action] = 0.0
                elif action == Action.INCREASE_INTERACTIVE:
                    Q[state][action] = -0.5

            elif is_cpu_heavy(state):
                if action == Action.INCREASE_CPU:
                    Q[state][action] = +0.1
                elif action == Action.DECREASE_CPU:
                    Q[state][action] = -0.05

    return Q



# def bucket_interactive(n):
#     if n == 0:
#         return 0  # Idle
#     elif n <= 2:
#         return 1  # Very few
#     elif n <= 5:
#         return 2  # Moderate
#     elif n <= 8:
#         return 3  # Many
#     else:
#         return 4  # Burst


def bucket_interactive(n):
    if n == 0:
        return 0  # Idle
    elif n == 1:
        return 1  # Very few
    elif n <= 3:
        return 2  # Moderate
    elif n <= 5:
        return 3  # Many
    else:
        return 4  # Burst

def bucket_cpu_heavy(cpu_heavy_exists):
    return 1 if cpu_heavy_exists else 0

# On these buckets, base them on how many ticks I change things.
def bucket_responsiveness(avg_latency):
    if avg_latency < 22:
        return 3  # Very responsive
    elif avg_latency < 45:
        return 2  # Moderate
    elif avg_latency < 70:
        return 1  # Slow
    else:
        return 0  # Very slow


def bucket_cpu_preempt_interval(avg_ticks):
    if avg_ticks < 15: # Very short (likely hurting throughput)
        return 0
    elif avg_ticks < 25:
        return 1  # Moderate
    elif avg_ticks < 50:
        return 2  # Long
    else:
        return 3  # Very long (likely under-utilizing preemption)


def calculate_reward(interactive_bucket, latency_score, cpu_util_score):
    w_inter, w_cpu = WEIGHT_TABLE[interactive_bucket]
    return (w_inter * latency_score) + (w_cpu * cpu_util_score)

def q_update(Q, last_state, last_action, reward, current_state, alpha=0.05, gamma=0.9):
    max_q_next = max(Q[current_state].values())
    current_q = Q[last_state][last_action]

    Q[last_state][last_action] = current_q + alpha * (reward + gamma * max_q_next - current_q)


def learn_on_preempt(Q, num_interactive, cpu_heavy_tasks, avg_latency, avg_cpu_preempt):
    global last_state
    global last_action
    global episodes
    episodes += 1
    # 1. Observe current state after task execution
    current_state = (
        bucket_interactive(num_interactive),
        bucket_cpu_heavy(cpu_heavy_tasks),
        bucket_responsiveness(avg_latency),
        bucket_cpu_preempt_interval(avg_cpu_preempt)
    )

    # 2. Calculate reward based on how task performed
    reward = calculate_reward(
        bucket_interactive(num_interactive),
        bucket_responsiveness(avg_latency),
        bucket_cpu_preempt_interval(avg_cpu_preempt))

    #

    # 3. Q-learning update
    q_update(Q, last_state, last_action, reward, current_state)

    # 4. Select new action for the current state
    new_action = choose_action(current_state, Q)
    # 5. Apply new action (e.g., change slice offset)
    apply_action(new_action)

    # 6. Store for next update
    last_state = current_state
    last_action = new_action

    #"step": self.tick_count,
    learning_log.append({
        "episode": episodes,
        "state": last_state,
        "action": Action(last_action).name,
        "reward": reward,
        "cpu_offset": globals.cpu_offset,
        "interactive_offset": globals.interactive_offset,
    })

    #print(
    #    f"[LEARN] state={last_state}, action={Action(last_action).name}, reward={reward:.3f}, next_state={current_state}, cpu_offset={globals.cpu_offset}, interactive_offset={globals.interactive_offset}")


def apply_action(action):
    base_slice = sysctl_sched_base_slice

    MIN_CPU_SLICE = base_slice
    MIN_INTERACTIVE_SLICE = 3

    MAX_CPU_OFFSET = 100
    #MAX_INTERACTIVE_OFFSET = 10
    MAX_INTERACTIVE_OFFSET = sysctl_sched_base_slice

    # Calculate minimum offsets from base
    MIN_CPU_OFFSET = MIN_CPU_SLICE - base_slice  #  -20 if base = 30
    MIN_INTERACTIVE_OFFSET = MIN_INTERACTIVE_SLICE - base_slice  # -27 if base = 30

    if action == Action.INCREASE_INTERACTIVE:
        globals.interactive_offset += 1
    elif action == Action.DECREASE_INTERACTIVE:
        globals.interactive_offset -= 1
    elif action == Action.INCREASE_CPU:
        globals.cpu_offset += 1
    elif action == Action.DECREASE_CPU:
        globals.cpu_offset -= 1
    elif action == Action.RESET_ALL:
        globals.interactive_offset = 0
        globals.cpu_offset = 0
    elif action == Action.PRIORITIZE_INTERACTIVE:
        globals.interactive_offset -= 1
        globals.cpu_offset -= 1

    # Clamp to safe minimums and maximums
    globals.interactive_offset = max(min(globals.interactive_offset, MAX_INTERACTIVE_OFFSET), MIN_INTERACTIVE_OFFSET)
    globals.cpu_offset = max(min(globals.cpu_offset, MAX_CPU_OFFSET),  MIN_CPU_OFFSET)

def choose_action(state, Q_table):
    """Choose an action based on epsilon-greedy strategy."""
    if random.random() < epsilon:
        # Exploration: pick a random action
        return random.randint(0, NUM_ACTIONS - 1)
    else:
        # Exploitation: pick the action with the highest Q-value
        best_action = 0
        best_value = Q_table[state][0]
        for action in range(1, NUM_ACTIONS):
            if Q_table[state][action] > best_value:
                best_value = Q_table[state][action]
                best_action = action
        return best_action