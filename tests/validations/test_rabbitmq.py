from alarmageddon.validations.rabbitmq import RabbitMqContext,\
    RabbitMqValidation
from alarmageddon.validations.exceptions import ValidationFailure
import pytest


class MockMethod:
    def __init__(self, count):
        self.message_count = count


class MockQueue:
    def __init__(self, count):
        self.method = MockMethod(count)


class MockChannel:
    def __init__(self, count):
        self.count = count

    def queue_declare(self, name, passive):
        return MockQueue(self.count)


@pytest.fixture(autouse=True)
def no_connect(monkeypatch):
    monkeypatch.setattr(RabbitMqValidation, "_connect",
                        lambda self: (None, MockChannel(200)))


def test_expected_queue_size():
    context = RabbitMqContext("host", 88, "name", "password")
    (RabbitMqValidation(context, "name", "queue", 500)
     .perform({}))


def test_expected_queue_size_correctly_fails():
    context = RabbitMqContext("host", 88, "name", "password")
    with pytest.raises(ValidationFailure):
        (RabbitMqValidation(context, "name", "queue", 100)
         .perform({}))
