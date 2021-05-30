class AnchorageInfo:
    """Contains information of an anchorage in the port"""

    def __init__(
            self,
            id: int,
            name: str,
            max_draught: float,
            use=""):
        """Initializes a new Anchorage Info

            :param id: anchorage Id.
            :param name: name of the anchorage.
            :param max_draught: max draught of the anchorage.
        """
        if id is None:
            raise ValueError("An anchorage ID is required!")

        if name is None:
            raise ValueError("An anchorage name is required!")

        if max_draught is None or type(max_draught) != float:
            raise ValueError("max_draught must be a float not None!")

        self.id = id
        self.name = name
        self.max_draught = max_draught
        self.use = use

    def __repr__(self):
        return (f"<AnchorageInfo: {self.name} | {self.max_draught} | "
                f"{self.use}>")
