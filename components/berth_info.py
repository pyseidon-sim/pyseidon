class BerthInfo:
    """Contains information of a Berth in the port"""

    def __init__(
        self,
        berth_id: int,
        name: str,
        max_quay_length: float,
        max_depth: float,
        allowed_vessel_content_type,
        section: str,
        **kwargs,
    ):
        """Initializes a new Berth Info

        :param berth_id: berth id.
        :param name: name of the berth.
        :param max_quay_length: max quay length of the berth.
        :param max_depth: max depth of the berth.
        :param allowed_vessel_content_type: content types of vessels allowed in the berth.
        :param section: the port section the berth belongs to
        """
        if not name:
            raise ValueError("A berth name is required!")

        if not max_depth or type(max_depth) != float:
            raise ValueError("max_depth must be a not None float!")

        if max_quay_length is not None and str(max_quay_length).strip() != "":
            self.max_quay_length = float(max_quay_length)
        else:
            self.max_quay_length = None
        self.id = berth_id
        self.name = name
        self.max_depth = max_depth
        self._allowed_vessel_content_type = allowed_vessel_content_type
        self.section = section

        # Add the rest of the arguments to class attributes
        self.__dict__.update(kwargs)

    def allowed_vessel_content_type(self):
        return self._allowed_vessel_content_type

    def get_color(self):
        """Returns the preferred colour for graphics"""
        return [0, 0, 0, 255]

    def __repr__(self):
        return (
            f"<BerthInfo: {self.name} | {self.max_quay_length} | "
            f"{self.max_depth} | {self._allowed_vessel_content_type}>"
        )
