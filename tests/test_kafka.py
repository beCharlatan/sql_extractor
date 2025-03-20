"""Test suite for Kafka integration with Allure reporting."""

import uuid
from unittest import mock

import allure
import pytest

from src.kafka.consumer import KafkaConsumer
from src.kafka.producer import KafkaProducer, send_sql_generation_request
from src.utils.errors import KafkaError


@allure.epic("Kafka Integration")
@allure.feature("Kafka Producer")
class TestKafkaProducer:
    """Test suite for the Kafka producer."""

    @pytest.fixture
    async def mock_producer(self):
        """Fixture for mocking the AIOKafkaProducer."""
        with mock.patch("src.kafka.producer.AIOKafkaProducer") as mock_producer_cls:
            mock_producer = mock.AsyncMock()
            mock_producer_cls.return_value = mock_producer
            yield mock_producer

    @allure.story("Producer Initialization")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_producer_init(self):
        """Test producer initialization."""
        bootstrap_servers = "test-server:9092"
        topic = "test-topic"

        producer = KafkaProducer(bootstrap_servers=bootstrap_servers, topic=topic)

        assert producer.bootstrap_servers == bootstrap_servers
        assert producer.topic == topic
        assert producer.producer is None

    @allure.story("Producer Start")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_producer_start(self, mock_producer):
        """Test starting the producer."""
        producer = KafkaProducer()
        await producer.start()

        mock_producer.start.assert_called_once()

    @allure.story("Producer Stop")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_producer_stop(self, mock_producer):
        """Test stopping the producer."""
        producer = KafkaProducer()
        producer.producer = mock_producer
        await producer.stop()

        mock_producer.stop.assert_called_once()

    @allure.story("Send Message")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_send_message(self, mock_producer):
        """Test sending a message."""
        producer = KafkaProducer()
        producer.producer = mock_producer

        filter_text = "products with price > 100"
        constraint_text = "sort by price desc"
        message_id = str(uuid.uuid4())

        result_id = await producer.send_message(
            filter_text=filter_text,
            constraint_text=constraint_text,
            message_id=message_id,
        )

        assert result_id == message_id
        mock_producer.send_and_wait.assert_called_once()
        # Check that the correct topic and message were used
        args, kwargs = mock_producer.send_and_wait.call_args
        assert kwargs["topic"] == producer.topic
        assert kwargs["value"]["filter"] == filter_text
        assert kwargs["value"]["constraint"] == constraint_text
        assert kwargs["value"]["message_id"] == message_id

    @allure.story("Send Message Error")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_send_message_error(self, mock_producer):
        """Test error handling when sending a message."""
        producer = KafkaProducer()
        producer.producer = mock_producer

        # Make the send_and_wait method raise an exception
        mock_producer.send_and_wait.side_effect = Exception("Test error")

        with pytest.raises(KafkaError):
            await producer.send_message(
                filter_text="test",
                constraint_text="test",
            )

    @allure.story("Convenience Function")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_send_sql_generation_request(self, mock_producer):
        """Test the convenience function for sending SQL generation requests."""
        filter_text = "products with price > 100"
        constraint_text = "sort by price desc"
        message_id = str(uuid.uuid4())

        with mock.patch("src.kafka.producer.KafkaProducer") as mock_producer_cls:
            mock_producer_instance = mock.AsyncMock()
            mock_producer_cls.return_value = mock_producer_instance
            mock_producer_instance.send_message.return_value = message_id

            result_id = await send_sql_generation_request(
                filter_text=filter_text,
                constraint_text=constraint_text,
                message_id=message_id,
            )

            assert result_id == message_id
            mock_producer_instance.start.assert_called_once()
            mock_producer_instance.send_message.assert_called_once_with(
                filter_text=filter_text,
                constraint_text=constraint_text,
                message_id=message_id,
                headers=None,
            )
            mock_producer_instance.stop.assert_called_once()


@allure.epic("Kafka Integration")
@allure.feature("Kafka Consumer")
class TestKafkaConsumer:
    """Test suite for the Kafka consumer."""

    @pytest.fixture
    async def mock_consumer(self):
        """Fixture for mocking the AIOKafkaConsumer."""
        with mock.patch("src.kafka.consumer.AIOKafkaConsumer") as mock_consumer_cls:
            mock_consumer = mock.AsyncMock()
            mock_consumer_cls.return_value = mock_consumer
            yield mock_consumer

    @allure.story("Consumer Initialization")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_consumer_init(self):
        """Test consumer initialization."""
        bootstrap_servers = "test-server:9092"
        topic = "test-topic"
        group_id = "test-group"

        consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            group_id=group_id,
        )

        assert consumer.bootstrap_servers == bootstrap_servers
        assert consumer.topic == topic
        assert consumer.group_id == group_id
        assert consumer.consumer is None

    @allure.story("Consumer Start")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_consumer_start(self, mock_consumer):
        """Test starting the consumer."""
        consumer = KafkaConsumer()
        await consumer.start()

        mock_consumer.start.assert_called_once()

    @allure.story("Consumer Stop")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_consumer_stop(self, mock_consumer):
        """Test stopping the consumer."""
        consumer = KafkaConsumer()
        consumer.consumer = mock_consumer
        consumer._running = True
        await consumer.stop()

        mock_consumer.stop.assert_called_once()
        assert not consumer._running
