from flask import Flask, request, jsonify
import pika
import json
import logging
from retrying import retry
from database import init_db, save_notification, get_user_notifications
import warnings

# Ignore unnecessary warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Setting up logging - just the important stuff
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING to reduce noise
    format="%(levelname)s: %(message)s",  # Simplified format
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.logger.setLevel(logging.ERROR)  # Only show errors from Flask

# Quick database setup
init_db()


# RabbitMQ connection setup
def get_rabbitmq_connection():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
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
    channel.queue_declare(queue="notifications", durable=True)

    # Convert notification data to JSON
    message = json.dumps(notification_data)

    channel.basic_publish(
        exchange="",
        routing_key="notifications",
        body=message,
        properties=pika.BasicProperties(delivery_mode=2),  # make message persistent
    )

    connection.close()


@app.route("/notifications", methods=["POST"])
def send_notification():
    """The main gateway for sending notifications to users"""
    data = request.json

    # Make sure we got something to work with
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    user_id = data.get("user_id")
    notification_type = data.get("type")
    content = data.get("content")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    if not notification_type:
        return jsonify({"error": "type is required"}), 400

    if not content:
        return jsonify({"error": "content is required"}), 400

    # Validate notification type
    valid_types = ["email", "sms", "in-app"]
    if notification_type not in valid_types:
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
        return jsonify({"error": str(e)}), 500


@app.route("/users/<int:user_id>/notifications", methods=["GET"])
def get_user_notifications_endpoint(user_id):
    """Inbox viewer - shows all notifications for a user"""
    try:
        # Pull their message history
        notifications = get_user_notifications(user_id)
        return jsonify({"user_id": user_id, "notifications": notifications}), 200

    except Exception as e:
        logger.error(f"Error retrieving notifications: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Just checking if we're still alive"""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Fire it up! Let the notifications flow
    app.run(debug=False)  # Set to False to reduce console output
