class Dispatcher:
    def __init__(self, current_process):
        # This is wrong isnt it?? Yes it is.
        self.current_process = current_process

    def dispatch(self, scheduler):
        """Runs the picked process from the scheduler"""
        #self.current_process.run(scheduler)
        scheduler.current_process.run(scheduler)
