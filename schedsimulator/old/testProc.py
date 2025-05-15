from schedsimulator.enums.process_status import TaskStatus


class PlaneProcess:
    def __init__(self, pid, start_y):
        self.value = pid
        self.pid = pid
        self.preempt_time = 10  # Fixed for round-robin, dynamic for Linux.
        self.burst_time = 12  # Create something random here later.
        self.status = TaskStatus.NEW  # Status first time.
        self.next = None  # Needed for Round-Robin
        self.prev = None  # Not needed for FIFO queue.

        ## Unique to plane animation
        self.first_time = True
        self.height = 0
        self.width = 0
        self.locx = 0
        self.locy = start_y  # Each plane starts at a different row
        self.counter = 0

    async def run(self, stdscr):
        """
        Async coroutine that animates the plane, yielding execution to the scheduler.
        """
        ROWS = 4
        DELAY_VAL = 0.1  # Adjust delay

        plane_picture = [
            "    ___       _  ",
            "| __\\_\\_o____/_| ",
            "<[___\\_\\_-----<  ",
            "|  o'            "
        ]

        def draw_plane(stdscr, locx, locy):
            for j in range(ROWS):
                try:
                    stdscr.addstr(locy + j, locx, plane_picture[j])
                except curses.error:
                    pass  # Prevent crash if drawing outside bounds

        def erase_plane(stdscr, locx, locy):
            """Erase only the part where the plane was, instead of clearing the whole screen."""
            for j in range(ROWS):
                try:
                    stdscr.addstr(locy + j, locx, " " * len(plane_picture[j]))
                except curses.error:
                    pass  # Prevent crash if drawing outside bounds

        def print_counter(stdscr, counter, locy):
            try:
                stdscr.addstr(locy + ROWS + 1, 0, f"Process {self.pid}: {counter} ")
            except curses.error:
                pass  # Prevent crash if window is too small

        curses.curs_set(0)  # Hide cursor

        if self.first_time:
            self.first_time = False
            self.height, self.width = stdscr.getmaxyx()
            self.locx = self.width  # Start at the right edge

        while True:
            erase_plane(stdscr, self.locx, self.locy)  # Erase only the old plane

            self.locx -= 1  # Move left
            if self.locx <= 0:
                self.locx = self.width - 1  # Wrap around

            draw_plane(stdscr, self.locx, self.locy)  # Draw at new position
            print_counter(stdscr, self.counter, self.locy)
            self.counter += 1

            stdscr.refresh()

            await asyncio.sleep(DELAY_VAL)  # Simulating delay
            await asyncio.sleep(0)  # Explicitly yield execution to other coroutines



import curses
import asyncio

class MathProcess:
    def __init__(self, pid, row):
        self.pid = pid
        self.counter = 0
        self.row = row  # The row where this process prints in the terminal

    async def run(self, stdscr):
        """
        Async coroutine that calculates sum of numbers recursively and yields execution.
        """
        DELAY_VAL = 0.1  # Simulation delay

        def print_counter(stdscr, counter, done):
            """Print the current counter or exited message."""
            try:
                stdscr.addstr(self.row, 0, f"Process {self.pid} (Math)      : ")
                if done:
                    stdscr.addstr(self.row, 24, "Exited")
                else:
                    stdscr.addstr(self.row, 24, f"{counter}")
            except curses.error:
                pass  # Prevent crash if screen size is too small

        async def rec(n):
            """Recursive sum function that yields execution at multiples of 37."""
            if n % 37 == 0:
                await asyncio.sleep(0)  # Yield execution

            if n == 0:
                return 0
            else:
                return n + await rec(n - 1)

        # Main loop
        for i in range(101):
            result = await rec(i)
            stdscr.addstr(10, 0, f"Did you know that 1 + ... + {i} = {result}")
            print_counter(stdscr, self.counter, False)
            self.counter += 1

            stdscr.refresh()
            await asyncio.sleep(DELAY_VAL)  # Simulate delay
            await asyncio.sleep(0)  # Yield execution

        print_counter(stdscr, self.counter, True)
        stdscr.refresh()


async def main(stdscr):
    """
    Initializes curses and runs multiple processes asynchronously in the same window.
    """
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()

    # Create multiple processes (planes + math process)
    processes = [
        PlaneProcess(1, start_y=2),
        PlaneProcess(2, start_y=8),
        PlaneProcess(3, start_y=14),
        MathProcess(4, row=24)  # Math process prints at row 24
    ]

    tasks = [p.run(stdscr) for p in processes]  # Create coroutine tasks

    await asyncio.gather(*tasks)  # Run all processes concurrently


if __name__ == "__main__":
    curses.wrapper(lambda stdscr: asyncio.run(main(stdscr)))  # ✅ Properly await the async function


