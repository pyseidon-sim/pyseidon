class MessageBroker:
    """Singleton class that can be used to send messages between entities."""
    __instance = None

    @staticmethod
    def get_instance():
        if MessageBroker.__instance == None:
            MessageBroker()
        
        return MessageBroker.__instance 

    def __init__(self):
        """Private constructor."""

        if MessageBroker.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            MessageBroker.__instance = self
            self._messages = {}

    def send_message(self, message):
        if message.destination not in self._messages:
            self._messages[message.destination] = []
        
        self._messages[message.destination].append(message)

    def remove_message(self, message_id, destination_queue):
        filtered_messages = list(filter(
            lambda x: x.id != message_id,
            self._messages[destination_queue]))

        self._messages[destination_queue] = filtered_messages

    def get_messages(self, receiver):
        return self._messages.get(receiver, [])

    def clear(self):
        self._messages = {}
