import namegenerator as ng


class VesselInfo:
    """Contains information of a Vessel in the port"""

    def __init__(
        self,
        length=0.0,
        width=0.0,
        max_draught=0.0,
        actual_draught=0.0,
        vessel_type=None,
        vessel_class=None,
        pilot_required=False,
        number_of_tugboats=0,
        **kwargs,
    ):
        """Initializes a new VesselInfo

        :param length: length of the vessel (default 0).
        :param width: width of the vessel (default 0).
        :param max_draught: max draught the vessel can have.
        :param actual_draught: actual draught of the vessel.
        :param vessel_type: type of the vessel (see example/example_model/VesselType).
        :param vessel_class: class of the vessel (see example/example_model/VesselClass).
        :param pilot_required: boolean representing if the boat requires pilot assistance (default False).
        :param number_of_tugboats: number of tugboats the boat needs (default 0).
        """
        self.name = ng.gen()
        self.length = length
        self.width = width

        self.max_draught = max_draught
        self.actual_draught = actual_draught

        self.vessel_type = vessel_type
        self.vessel_class = vessel_class

        self.pilot_required = pilot_required
        self.number_of_tugboats = number_of_tugboats

        # Add the rest of the arguments to class attributes
        self.__dict__.update(kwargs)

    @property
    def tugs_required(self):
        return self.number_of_tugboats > 0

    def __repr__(self):
        return (
            f"<VesselInfo: {self.name} | {self.length} | {self.width} | "
            f"{self.vessel_type} | {self.vessel_class} | "
            f"{self.actual_draught} (max: {self.max_draught}) | {self.number_of_tugboats} "
            f" tugboat(s) | pilot: {self.pilot_required} | {self.vessel_type}>"
        )
