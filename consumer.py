import pika
import json
import time
import logging
import warnings
from notification_services import get_notification_service
from database import update_notification_status
from config import (
    LOG_LEVEL,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_QUEUE,
    RABBITMQ_URL,
)

# Quiet those pesky warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Keep logging minimal - just what we need to know
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(levelname)s: %(message)s",  # Cleaner format
)
logger = logging.getLogger(__name__)


def get_rabbitmq_connection():
    """Get a connection to RabbitMQ"""
    # Use URL-based connection if available, otherwise use parameters
    if RABBITMQ_URL:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    else:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
            )
        )
    return connection


def process_notification(ch, method, properties, body):
    """
    Handles notifications coming from the queue

    Takes care of:
    - Checking if the message makes sense
    - Sending it through the right channel
    - Telling RabbitMQ we're done with it
    """
    try:
        # Check if body is empty
        if not body:
            logger.warning("Received empty message body. Acknowledging and skipping.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Parse the notification
        notification_data = json.loads(body)

        # Validate essential fields
        notification_id = notification_data.get("id")
        user_id = notification_data.get("user_id")
        notification_type = notification_data.get("type")
        content = notification_data.get("content")

        if not all([notification_id, user_id, notification_type, content]):
            logger.warning(
                f"Received incomplete notification data: {notification_data}. Acknowledging and skipping."
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info(
            f"Processing {notification_type} notification {notification_id} for user {user_id}"
        )

        # Get the appropriate notification service
        service = get_notification_service(notification_type)

        # Send the notification
        success = service.send(user_id, content)

        if success:
            # Update the notification status in the database
            update_notification_status(notification_id, "delivered")
            logger.info(f"Notification {notification_id} delivered successfully")
        else:
            # Update the notification status in the database
            update_notification_status(notification_id, "failed")
            logger.error(f"Failed to deliver notification {notification_id}")

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        logger.error(
            f"Invalid JSON in message: {str(e)}. Message content: '{body.decode('utf-8', errors='replace')}'"
        )
        # Don't requeue invalid JSON messages as they will never process correctly
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
        # Negative acknowledgment with requeue for other errors
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer():
    """Wake up our message handler and start listening"""

    # Knock knock, RabbitMQ
    connection = get_rabbitmq_connection()
    channel = connection.channel()  # Make sure our queue exists
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    # One at a time please - we're not in a rush
    channel.basic_qos(prefetch_count=1)  # Tell RabbitMQ to call us when messages arrive
    channel.basic_consume(
        queue=RABBITMQ_QUEUE, on_message_callback=process_notification
    )

    logger.info("🔔 Notification handler is awake and listening...")

    # Start consuming messages
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    connection.close()


if __name__ == "__main__":
    # Let's get this notification party started!
    start_consumer()
