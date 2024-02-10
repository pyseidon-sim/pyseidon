from .vessel_class import VesselClass


class MockBerthServiceDistributionFactory:
    def service_time_sampler(self, terminal_name):
        """Static service time of 100 seconds"""
        return lambda vessel_info: 100

    def get_allowed_vessel_classes_for_terminal(self, terminal_name):
        return [c for c in VesselClass]
