# import random
#
# Q = {}  # Q-table: state -> action -> value
# alpha = 0.1
# gamma = 0.9
# epsilon = 0.1
#
#
# # Ok, here is my plan for now
# # action -> -0.1, 0, 0.1   (so just change the weights in the calulation of the virtual deadlines in EEVDF)
# # state -> different parameters for the scheduler, so summerised state.
# # - avg_throughput (low, med, high)
# # - avg_wait_time (low, med, high)
# # - avg_turnaround_time (low, med, high)
# # - (some starvation parameter)
# # -
# #
# #
# # This is how it will be stored:
# #Q[(0, 0)] = { -0.1: 0.5, 0.0: 0.2, +0.1: -0.1 }
# #Q[(0, 1)] = { -0.1: 0.1, 0.0: 0.3, +0.1: 0.0 }
# #Q[(2, 2)] = { -0.1: -0.8, 0.0: -0.5, +0.1: -0.2 }
# # ... 6 other states like this, if we have 9 combinations.
# # Then ok, this is how its stored.
# # Now we need a reward system.
# #
# #
# #
# #
# #
#
#
# def choose_action(state, actions):
#     if random.random() < epsilon:
#         return random.choice(actions)
#     if state not in Q:
#         Q[state] = {a: 0 for a in actions}
#     return max(Q[state], key=Q[state].get)
#
# def update_q(state, action, reward, next_state, next_actions):
#     if next_state not in Q:
#         Q[next_state] = {a: 0 for a in next_actions}
#     best_next = max(Q[next_state].values())
#     Q[state][action] += alpha * (reward + gamma * best_next - Q[state][action])


#### ---------------- new ---------------------
import random

# Constants
NUM_STATES = 160
NUM_ACTIONS = 5


# Parameters
# alpha = 0.1        # Learning rate
# gamma = 0.9        # Discount factor
# epsilon = 0.1      # Exploration probability

alpha = 0.05        # Learning rate
gamma = 0.9       # Discount factor
epsilon = 0.01


# Define possible states (state as a tuple: (interactive_bucket, cpu_bound_bucket, responsiveness_bucket, throughput_bucket))
interactive_buckets = [0, 1, 2, 3, 4]  # Idle, Very few, Moderate, Many, Burst
cpu_bound_buckets = [0, 1]              # 0 (none) or 1 (one or more CPU-heavy)
responsiveness_buckets = [0, 1, 2, 3]       # Low, Moderate, High, Very High
throughput_buckets = [0, 1, 2, 3]        # Low, Moderate, High, Very High

# Define possible actions
# Figure out how much we should increase or decrease weight
actions = {
    0: 0,    # keep weight
    1: 1,  # decrease CPU_weight
    2: 1,  # increase CPU_weight
    3: 1,  # decrease Interactive weight
    4: 1  # increase interactive weight
}

# Build empty Q-table
Q_table = {}


# Initialize Q-table: for every state, for every action, set Q-value to 0.0
# for interactive in interactive_buckets:
#     for cpu_bound in cpu_bound_buckets:
#         for responsiveness in responsiveness_buckets:
#             for throughput in throughput_buckets:
#                 state = (interactive, cpu_bound, responsiveness, throughput)
#                 for action in actions.keys():
#                     Q[(state, action)] = 0.0

# Pseudocode for Q-table seeding

# Initialize Q-table with all entries 0
Q_table = {}  # Dictionary or 2D array

# for state in all_states:
#     for action in all_actions:
#         Q_table[(state, action)] = 0.0  # Default neutral value
#
#     # Then: based on the state, seed the "best" action
#     best_action = choose_best_action_for_state(state)  # <- Your prior knowledge
#     Q_table[(state, best_action)] = 0.1  # Seed slightly positive value
#
#     # (Optional) Also seed "bad" actions slightly negative
#     bad_action = choose_bad_action_for_state(state)  # <- Your knowledge
#     Q_table[(state, bad_action)] = -0.05  # Seed slightly negative value


# This happens inside a training loop.
state = (2, 1, 0, 3)          # Example current state
action = 2                   # Example action (increase_weight)
reward = 1.0                 # Example reward received
next_state = (3, 1, 0, 2)     # Example next state

def q_learning_update(Q, state, action, reward, next_state, alpha=0.1, gamma=0.9):
    """
    Update the Q-table based on observed transition.

    Args:
    - Q: The Q-table (dict)
    - state: Current state (tuple)
    - action: Action taken (int)
    - reward: Observed reward (float)
    - next_state: Next state after action (tuple)
    - alpha: Learning rate
    - gamma: Discount factor
    """
    # Find the best next action from next_state
    max_future_q = max(Q[(next_state, a)] for a in actions.keys())

    # Current Q-value
    current_q = Q[(state, action)]

    # Q-learning update rule
    Q[(state, action)] = current_q + alpha * (reward + gamma * max_future_q - current_q)

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


q_learning_update(Q_table, state, action, reward, next_state, alpha=alpha, gamma=gamma)
print(f"Initialized Q-table with {len(Q)} entries.")

# Initial system state (example starting point)
current_state = get_current_system_state()

# Training loop
while True:

    # --- Step 1: Choose Action ---
    action = choose_action(current_state)

    # --- Step 2: Apply Action ---
    apply_action(action)  # Adjust base slice based on chosen action

    # Let the system run for a short period (simulate scheduling interval)
    simulate_system_run(duration=TIME_WINDOW)

    # --- Step 3: Observe new state ---
    next_state = get_current_system_state()

    # --- Step 4: Compute Reward ---
    reward = calculate_reward()

    # --- Step 5: Update Q-table ---
    update_q_table(current_state, action, reward, next_state)

    # --- Step 6: Transition to next state ---
    current_state = next_state