import curses
import time

from schedsimulator.enums.process_status import TaskStatus


class PlaneProcess:
    # TODO Lagre context i klassen, alle variabler jeg trenger for at denne skal kjøre.

    def __init__(self, pid):
        self.value = pid
        self.pid = pid
        self.preempt_time = 10  # Fixed for round-robin, dynamic for linux.
        self.burst_time = 12  # Create something random here later.
        self.status = TaskStatus.NEW  # Status first time.
        self.next = None  # Next
        self.prev = None  # Trenger ikke denne på FIFO Queue. Trenger den til RoundRobin

        ## Unique
        self.curs_set = 0
        self.first_time = True
        self.hight = 0
        self.width = 0
        self.locx = 0
        self.locy = 1
        self.counter = 0


    async def run(self, scheduler):
        ROWS = 4
        DELAY_VAL = 0.1  # Adjust delay for Python equivalent

        plane_picture = [
            "    ___       _  ",
            "| __\\_\\_o____/_| ",
            "<[___\\_\\_-----<  ",
            "|  o'            "
        ]

        def draw_plane(stdscr, locx, locy):
            for j in range(ROWS):
                stdscr.addstr(locy + j, self.locx, plane_picture[j])

        def print_counter(stdscr, counter):
            if 10 < curses.LINES:  # Ensure there's enough space to print
                stdscr.addstr(10, 0, f"Process 1 (Plane)     : {counter}")
                #stdscr.refresh()

        def plane_simulation(stdscr):
            curses.curs_set(1)
            if self.first_time:
                stdscr.clear()
                self.first_time = False
                self.height, self.width = stdscr.getmaxyx()
                self.locx = self.width

            for _ in True:
                stdscr.clear()
                print_counter(stdscr, self.counter)
                self.locx -= 1
                if self.locx <= 0:
                    self.locx = self.width - 1
                draw_plane(stdscr, self.locx, self.locy)
                print_counter(stdscr, self.counter)
                self.counter += 1
                time.sleep(DELAY_VAL)  # Simulating delay

                scheduler.yields()


        curses.wrapper(plane_simulation)



