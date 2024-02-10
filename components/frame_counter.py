class FrameCounter:
    """A counter class that can be used to count/track the frames/simulation ticks."""

    def __init__(self, **kwargs):
        # Add the rest of the arguments to class attributes
        self.__dict__.update(kwargs)

        self._count = 0

    def reset(self):
        self._count = 0

    def increase(self):
        self._count += 1

    def get_count(self):
        return self._count

    def __repr__(self):
        return f"<FrameCounter: {self._count}>"
