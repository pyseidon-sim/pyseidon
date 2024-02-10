class TimerScheduler:
    world = None
    __instance = None

    @staticmethod
    def get_instance():
        if TimerScheduler.__instance == None:
            TimerScheduler()

        return TimerScheduler.__instance

    def __init__(self):
        """Private constructor."""
        if TimerScheduler.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            TimerScheduler.__instance = self

    def schedule(self, timer):
        if not self.world:
            raise Exception("The timer creator was not supplied a world!")

        timer_entity = self.world.create_entity()
        self.world.add_component(timer_entity, timer)
