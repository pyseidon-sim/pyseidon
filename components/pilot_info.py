import namegenerator as ng


class PilotInfo:
    """Contains information of a pilot in the port"""

    def __init__(
            self,
            length=0.0,
            width=0.0,
            max_draught=0.0,
            actual_draught=0.0,
            **kwargs):
        """Initializes a new PilotInfo

        :param length: length of the pilot vessel (default 0).
        :param width: width of the pilot vessel (default 0).
        :param max_draught: max draught the pilot vessel can go on.
        :param actual_draught: actual draught of the pilot vessel.
        """

        self.name = ng.gen()
        self.length = length
        self.width = width

        self.max_draught = max_draught
        self.actual_draught = actual_draught

        # Add the rest of the arguments to class attributes
        self.__dict__.update(kwargs)
    
    def __repr__(self):
        return (f"<PilotInfo: {self.name} | {self.length} | {self.width} | "
                f"{self.actual_draught} (max: {self.max_draught})>")