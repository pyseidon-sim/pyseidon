class BaseVesselAnomaly:
    """Base class for vessel anomalies. Derive this class to create any anomalies related to vessels."""

    def check_for_anomaly(self, entity_id):
        """Returns whether an anomaly needs to be generated.

        :return: bool
        """
        raise NotImplementedError()

    def execute_anomaly(self, entity_id):
        """This method executes the anomaly in question.

        It should probably be executed after check_for_anomaly() returns true.
        """
        raise NotImplementedError()
