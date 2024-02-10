"""
    Tests the functionality of the message broker and the
    SimulationMessage class
"""

import pytest

from environment.messaging import MessageBroker, SimulationMessage

from .constants import TEST_RECEIVER


@pytest.fixture()
def message_broker():
    broker = MessageBroker.get_instance()
    broker.clear()

    return broker


@pytest.fixture()
def mock_message():
    return SimulationMessage(
        sender="test-sender", destination=TEST_RECEIVER, message="lorem"
    )


def test_message_flow(message_broker, mock_message):
    """
    Tests sending and receiving messages
    """
    message_broker.send_message(mock_message)
    assert len(message_broker.get_messages(TEST_RECEIVER)) == 1

    # Remove the sent message from the receiver queue
    message_broker.remove_message(mock_message.id, TEST_RECEIVER)
    # Verify that the message has been removed
    assert len(message_broker.get_messages(TEST_RECEIVER)) == 0


def test_clear(message_broker, mock_message):
    message_broker.send_message(mock_message)
    assert len(message_broker.get_messages(TEST_RECEIVER)) == 1

    message_broker.clear()
    assert len(message_broker.get_messages(TEST_RECEIVER)) == 0


def test_message_entities():
    message = SimulationMessage(
        sender="ent:1234", destination=TEST_RECEIVER, message="lorem"
    )

    assert message.sender_entity_id == 1234
    assert message.destination_entity_id is None

    message.destination = "ent:lorem"

    # This should raise an exception since the entity id
    # is not numeric
    with pytest.raises(ValueError):
        message.destination_entity_id
