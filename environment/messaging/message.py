import uuid


class SimulationMessage:
    """Represents a message between two entities or systems in the simulation.

    The sender and receiver fields should be formatted as
    `entity_type:entity_id` or as `system_name`

    data is a dictionary holding any extra data attached to the message
    """

    def __init__(self, sender, destination, message, data=None):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.message = message
        self.destination = destination
        self.data = data

    @property
    def sender_entity_id(self):
        return self._get_id_from_string(self.sender)

    @property
    def destination_entity_id(self):
        return self._get_id_from_string(self.destination)

    def _get_id_from_string(self, in_string):
        """Returns the id of a string in the format text:id

        If the string is not in the correct format None
        will be returned.
        """
        comps = in_string.split(":")

        if len(comps) > 1:
            return int(comps[1])

        return None

    def __repr__(self):
        return f"<Message from {self.sender} to {self.destination}: {self.message}>"
