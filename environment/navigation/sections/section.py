class Section:
    """
    Class representing a section in the port. A section
    is an area of the port where certain rules apply.
    """

    def __init__(
        self,
        name,
        shape,
        is_ocean=False,
        vessel_speeds=None,
        default_speeds={"min": 0.0, "max": 15.0},
        **kwargs,
    ):
        """Initializes a Section

        Arguments:
        :params name: name of the section
        :params shape: shapely polygon of the section area
        :params is_ocean: whether the section is the ocean/sea
        :params vessel_speeds: dictionary in the form

        {
            VesselClass.CLASS_1: {
                "min": 0.0,
                "max": 15.0
            }, ...
        }

        :params default_speeds: speed limits applied to all vessels if
                                vessel_speeds is not provided
        """
        assert name is not None, "A section must have a name!"
        if shape is None and not is_ocean:
            raise ValueError("A non-ocean section must have a shape!")

        self.name = name
        self.shape = shape
        self.default_speeds = default_speeds
        self.vessel_speeds = vessel_speeds

        # Add the rest of the arguments to class attributes
        self.__dict__.update(kwargs)

    def speeds_for_class(self, vessel_class):
        if self.vessel_speeds is None or vessel_class not in self.vessel_speeds:
            return self.default_speeds

        return self.vessel_speeds[vessel_class]

    def __repr__(self):
        return f"<SectionInfo: {self.name}>"
