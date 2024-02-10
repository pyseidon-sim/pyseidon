class SectionLogger:
    """Class to log port section information."""

    def __init__(self):
        self.logs = []

    def add_log(self, section, timestamp):
        self.logs.append([section.name, timestamp])

    def header(self):
        return [["name", "timestamp"]]

    def clear(self):
        self.logs = []
