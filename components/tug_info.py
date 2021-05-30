import namegenerator as ng


class TugInfo:
    """Contains information of a tugboat in the port"""

    def __init__(
            self,
            length=0.0,
            width=0.0,
            max_draught=0.0,
            actual_draught=0.0,
            **kwargs):
        """Initializes a new TugInfo
        
        :param length: length of the tug (default 0).
        :param width: width of the tug (default 0).
        :param max_draught: max draught the tug can go on.
        :param actual_draught: actual draught of the tug.
        """
        self.name = ng.gen()
        self.length = length
        self.width = width
        
        self.max_draught = max_draught
        self.actual_draught = actual_draught

        # Add the rest of the arguments to class attributes
        self.__dict__.update(kwargs)

    def __repr__(self):
        return (f"<TugInfo: {self.name} | {self.length} | {self.width} | "
                f"{self.actual_draught} (max: {self.max_draught})>")
