# SchedulerSimulatorLinuxOS

## Project Context

This project started with the broad goal:  
**“Improve scheduling with Artificial Intelligence (AI)”**

Through the research process, this goal evolved into the focused objective:  
**“Enhancing the Linux EEVDF Scheduler with Tabular Q-Learning”**

This repository contains the simulation code, experiments, and configurations that support this study.


## Known Issues & Clarifications

- There are some known mistakes in the thesis regarding:
  - Design: 
    - Mistakes in section 4.2.2 in the design chapter in the thesis. 
      - "Average throughput for CPU-bound tasks", should be "Average CPU utilisation for CPU-bound tasks"
      - I accidentally changed the wording from ‘slice offset’ to ‘latency offset in section 4.2.2 subsection "Action Space" (should also ideally be a subsection, not subsubsection). I also write "increase latency offset", where is should be "decrease base-slice offset" 
        - The code in this repository and algorithm 9 shows what actions are really taken.
    - Learning episodes in section 4.2.4
      - I write "The agent starts with an empty Q-table where all values are set to zero.", this is not correct, it is pre initialised as explained in the next subsection. 
  - Results
    - Evaluation setup 6.3.1: 
      - Wrote "per-task latency for interactive tasks", meant "average latency for interactive tasks"
    - Scenario results 6.3.2: 
      - Interactive max clamp is 30 (base_slice), not 10.


I include this here to clear potential confusion from what is written and what is actually done. 

## Description

SchedulerSimulatorLinuxOS is a Python-based simulator designed to mimic the current Linux EEVDF process scheduling behavior.  


## Setup

**Important Note:**  
This simulator uses Unix signals (via Python’s `signal` module), which are not fully supported on Windows.  
The implementation has only been tested on macOS. Running it on Linux should work the same way,  
but I am not sure how to run it on Windows. 

1. Create virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. Install all required packages:
    ```bash
    pip install -r requirements.txt
    ```

3. Run the simulator:
    ```bash
    python3 main.py
    ```

4. Run tests:
    ```bash
    pytest
    ```
 
## Code Overview

Below is a quick guide to where you can find the main components in this repository:

For the main EEVDF logic: 
- **`schedsimulator/eevdf_first_sched`**  
  - Contains the core EEVDF scheduling implementation logic
  - Here you find the scheduling loop, context switch, preempts, heap for sleeping tasks etc. 
- **`schedsimulator/enqueue_task`**  
  - The EEVDF enqueue logic for the scheduler
- **`schedsimulator/dequeue_task`**  
  - The EEVDF dequeue logic for the scheduler
- **`schedsimulator/pick_next_task_fair`**  
  - The EEVDF logic for picking the next task in the red-black tree (runqueue)
- **`schedsimulator/task_tick`**  
  - The EEVDF logic for advancing time in the tasks when ticks happen in `preempt_handler`
- **`schedsimulator/update_current`**  
  - The EEVDF logic for updating the tasks virtual time and deadline when time advances. 
- **`schedsimulator/wakeup_preempt`**  
  - The EEVDF logic for waking up tasks. 
- **`schedsimulator/utils`**  
  - More EEVDF logic used in more places and files in the code: `avg_vruntime_add`, `avg_vruntime_sub`, `calc_delta_fair`, `entity_key`, `avg_vruntime`, `avg_vruntime_update`, `__update_min_vruntime`, `update_min_vruntime`, `vruntime_eligible`, `entity_eligible`, `entity_before`, `protect_slice`, `pick_root_entity`

Configuration:
- **`schedsimulator/globals.py`**  
  Defines all global configuration parameters (time slice, tick duration, task counts, adaptive toggle, etc.)

For the tabular Q-learner: 
- **`schedsimulator/tabular_q_learner.py`**
  - Defines the Q-learning algorithm and learning loop. 
- **`schedsimulator/q_state_config.py`**
  - Used for the state and config for the q-learner. 

Structures
- **`schedsimulator/structures/`**
  - **`task.py`** define the tasks in the simulation, I/O, interactive, and CPU bound. 
  - **`cfs_rq.py`** defines the runqueue in the simulation. 
  - **`red_black_tree.py`** the red black tree implementation used in the simulation. 

Enums: 
- **`schedsimulator/enums/`**
  - Defininig task type, and process status. 

Exceptions: 
- **`schedsimulator/exceptions/`**
  - Exception for dead greenlets. 

Extra: 
- **`schedsimulator/RRScheduler`** 
  - A round-robin scheduler implementation which was used for testing. 
- **`schedsimulator/old`** 
  - A Lot of old material and tests implemented in the earlier phases of this master thesis. 
- **`schedsimulator/processes/`**
  - Old material not used, you can find the task used in structures, this is old material. 

Tests: 
- **`tests/`**  
  Contains unit tests for the Red-Black Tree (can be run with `pytest`)
  
## Configuration
In main.py you choose how many times you want to run the simulation. Change the `num_runs` variable. This was set to 10 on all experiments. 
The main parameters for this simulation are defined in **`globals.py`**. Some configuration for the q-learner is in **`q_state_config.py`** and in **`tabular_q_learner.py`** 
You can adjust these values to modify the workload and scheduling behavior. The only adjustments needed to change for running the scenarioes is done in **`globals.py`**. 

For printing the plots after running the experiments: 
```bash
python3 q_learner_plots.py
```

Configurations for scenario 1:
```python
# Tasks: 
NUM_INTERACTIVE = 12
NUM_CPU = 4
NUM_IO = 4

# Other
EXIT_COUNT = 20
INTERACTIVE_TIME_WINDOW = 100
ADAPTIVE = True # Set the adaptive version to true for testing the adaptive version, and false for testing normal EEVDF
```

- Interactive tasks run for 300 ticks
- CPU bound tasks run for 1200 ticks
- I/O bound for 300 ticks

Configurations for scenario 2:
```python
# Tasks: 
NUM_INTERACTIVE = 3
NUM_CPU = 7
NUM_IO = 10

# Other
EXIT_COUNT = 20
INTERACTIVE_TIME_WINDOW = 100
ADAPTIVE = True # Set the adaptive version to true for testing the adaptive version, and false for testing normal EEVDF
```

- Interactive tasks run for 300 ticks
- CPU bound tasks run for 1000 ticks
- I/O bound for 600 ticks
- To run it like it was run in the thesis, you need to add the extra count bug in enqueue and dequeue.
  - If you run without, it actually runs very similar, so there is actually no need to run like in the thesis with the bug.
  - It shows the same resuslts in a way, the stats are similar, and behave relativly the same.

Configurations for scenario 3:
```python
# Tasks: 
NUM_INTERACTIVE = 0
NUM_CPU = 14
NUM_IO = 4

# Other
EXIT_COUNT = 18
INTERACTIVE_TIME_WINDOW = 100
ADAPTIVE = True # Set the adaptive version to true for testing the adaptive version, and false for testing normal EEVDF
```

- CPU bound tasks run for 1200 ticks
- I/O bound for 300 ticks
- NOTE: If you want to test this just run with 16 cpu heavy tasks and 4 I/O, it will show the same, then you do not need to change the exit count.


## Features

- Schedulers (Round Robin, EEVDF, and Adaptive EEVDF with tabular Q-learning)
- Red-Black Tree used for the EEVDF run queue
- Simulation of Interactive, I/O and CPU-bound tasks
- Signals for simulating timer preemption
- Heap for sleep queue
- Test red-black tree via `pytest`
- `q_learner_plots.py` for printing the q-learning plots. 

## Testing
Tests are located in the `tests/` folder and cover:
- Tree insertion, deletion and red-black balancing
- Min vruntime on enqueue and dequeue

Run tests using:
```bash
pytest
```

## Debugging 

If you want to print the red-black tree values in a certain position in the code, you can print it like this: 
```python
cfs_rq.task_timeline.print_tree()
```

## Context

This simulator is part of my Master's thesis, exploring the effectiveness of Adaptive EEVDF version with tabular Q-learning versus the current Linux version of the EEVDF scheduler. 
It replicates realistic CPU behavior in Python, with blocking mechanisms for sleep, timer preeempts with signals and context switch with the use of greenlets. 
