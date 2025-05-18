from flask import Flask, request, jsonify, Response
import pika
import json
import logging
from retrying import retry
from database import init_db, save_notification, get_user_notifications
import warnings
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from config import (
    API_HOST,
    API_PORT,
    DEBUG,
    LOG_LEVEL,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_URL,
    RABBITMQ_QUEUE,
)

# Ignore unnecessary warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Setting up logging - just the important stuff
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(levelname)s: %(message)s",  # Simplified format
)
logger = logging.getLogger(__name__)

# Define Prometheus metrics
NOTIFICATIONS_SENT = Counter(
    "notifications_sent_total", "Total number of notifications sent", ["type"]
)
NOTIFICATION_DURATION = Histogram(
    "notification_processing_seconds", "Time spent processing notification requests"
)
API_REQUESTS = Counter(
    "api_requests_total", "Total API requests", ["endpoint", "method", "status"]
)
QUEUE_ERRORS = Counter("queue_errors_total", "Total number of queue errors")

app = Flask(__name__)
app.logger.setLevel(logging.ERROR)  # Only show errors from Flask

# Quick database setup
init_db()


# RabbitMQ connection setup
def get_rabbitmq_connection():
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


# Retry logic for failed notifications
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def send_to_queue(notification_data):
    """
    Send a notification to the RabbitMQ queue

    Args:
        notification_data (dict): Notification data including id, user_id, type, and content
    """
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(
        queue=RABBITMQ_QUEUE, durable=True
    )  # Convert notification data to JSON
    message = json.dumps(notification_data)

    channel.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),  # make message persistent
    )

    connection.close()


@app.route("/notifications", methods=["POST"])
def send_notification():
    """The main gateway for sending notifications to users"""
    start_time = time.time()
    data = request.json

    # Make sure we got something to work with
    if not data:
        API_REQUESTS.labels(
            endpoint="/notifications", method="POST", status="400"
        ).inc()
        return jsonify({"error": "Request body is required"}), 400

    user_id = data.get("user_id")
    notification_type = data.get("type")
    content = data.get("content")

    if not user_id:
        API_REQUESTS.labels(
            endpoint="/notifications", method="POST", status="400"
        ).inc()
        return jsonify({"error": "user_id is required"}), 400

    if not notification_type:
        API_REQUESTS.labels(
            endpoint="/notifications", method="POST", status="400"
        ).inc()
        return jsonify({"error": "type is required"}), 400

    if not content:
        API_REQUESTS.labels(
            endpoint="/notifications", method="POST", status="400"
        ).inc()
        return jsonify({"error": "content is required"}), 400

    # Validate notification type
    valid_types = ["email", "sms", "in-app"]
    if notification_type not in valid_types:
        API_REQUESTS.labels(
            endpoint="/notifications", method="POST", status="400"
        ).inc()
        return jsonify({"error": f"type must be one of: {', '.join(valid_types)}"}), 400

    try:
        # Save the notification to the database
        notification_id = save_notification(user_id, notification_type, content)

        # Prepare notification data for the queue
        notification_data = {
            "id": notification_id,
            "user_id": user_id,
            "type": notification_type,
            "content": content,
        }

        # Send the notification to the queue
        send_to_queue(notification_data)

        NOTIFICATIONS_SENT.labels(type=notification_type).inc()
        API_REQUESTS.labels(
            endpoint="/notifications", method="POST", status="200"
        ).inc()
        NOTIFICATION_DURATION.observe(time.time() - start_time)

        return (
            jsonify(
                {
                    "message": "Notification sent successfully",
                    "notification_id": notification_id,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        QUEUE_ERRORS.inc()
        API_REQUESTS.labels(
            endpoint="/notifications", method="POST", status="500"
        ).inc()
        return jsonify({"error": str(e)}), 500


@app.route("/users/<int:user_id>/notifications", methods=["GET"])
def get_user_notifications_endpoint(user_id):
    """Inbox viewer - shows all notifications for a user"""
    try:
        # Pull their message history
        notifications = get_user_notifications(user_id)
        API_REQUESTS.labels(
            endpoint="/users/<user_id>/notifications", method="GET", status="200"
        ).inc()
        return jsonify({"user_id": user_id, "notifications": notifications}), 200

    except Exception as e:
        logger.error(f"Error retrieving notifications: {str(e)}")
        API_REQUESTS.labels(
            endpoint="/users/<user_id>/notifications", method="GET", status="500"
        ).inc()
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Just checking if we're still alive"""
    API_REQUESTS.labels(endpoint="/health", method="GET", status="200").inc()
    return jsonify({"status": "ok"}), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    """Endpoint to expose Prometheus metrics"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    # Fire it up! Let the notifications flow
    app.run(host=API_HOST, port=API_PORT, debug=DEBUG)
