# SchedulerSimulatorLinuxOS

## Description

SchedulerSimulatorLinuxOS is a Python-based simulator designed to mimic Linux process scheduling behavior. It supports configurable scheduling algorithms and simulates how processes are selected, run, and blocked — useful for understanding low-level OS design or testing AI-enhanced schedulers.


## Setup

1. Create virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

2. Install all required packages:
    ```bash
    pip install -r requirements.txt
    ```

3. Run the simulator:
    ```bash
    python main.py
    ```

4. Run tests:
    ```bash
    pytest
    ```
   
## Features

- Red-Black Tree used for run queue (like Linux CFS)
- Multiple schedulers (Round Robin, FCFS, CFS, etc.)
- Visual/CLI interface using `blessed` or PyQt6
- Process generation and blocking simulation
- Testable via `pytest`


## Testing

Tests are located in the `tests/` folder and cover:
- Tree insertion and red-black balancing
- Process queue behavior
- Edge cases like repeated values or blocking behavior

Run tests using:
```bash
pytest
```

## Context

This simulator is part of my Master's thesis, exploring the effectiveness of AI-based scheduling versus traditional schedulers. 
It replicates realistic CPU behavior in Python, with blocking mechanisms and performance measurement tools.
