from pymongo import MongoClient
import json
import datetime
import warnings
from bson.objectid import ObjectId

# Quiet down the MongoDB warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Hook up to our database
client = MongoClient("mongodb://localhost:27017/")
db = client["notification_service"]
notifications_collection = db["notifications"]


def init_db():
    """
    Nothing to do here - MongoDB is cool like that
    
    No need for complicated setup steps, tables, or schemas
    MongoDB just creates stuff on the fly
    """
    # MongoDB is lazy (in a good way)
    pass


def save_notification(user_id, notification_type, content):
    """
    Store a notification in MongoDB

    Args:
        user_id (int): ID of the user receiving the notification
        notification_type (str): Type of notification (email, sms, in-app)
        content (str): Content of the notification

    Returns:
        str: ID of the inserted notification
    """
    notification = {
        "user_id": user_id,
        "type": notification_type,
        "content": content,
        "status": "pending",
        "created_at": datetime.datetime.now(),
    }

    result = notifications_collection.insert_one(notification)
    return str(result.inserted_id)


def update_notification_status(notification_id, status):
    """
    Mark a notification as delivered or failed
    
    Just needs:
    - which notification (by ID)
    - what happened to it (status)
    """
    notifications_collection.update_one(
        {"_id": ObjectId(notification_id)}, {"$set": {"status": status}}
    )


def get_user_notifications(user_id):
    """
    Pull up all the notifications for someone
    
    Just give it a user ID and it'll fetch everything
    they've been sent, newest first
    """
    cursor = notifications_collection.find({"user_id": user_id}).sort("created_at", -1)
    notifications = []

    for doc in cursor:
        notification = {
            "id": str(doc["_id"]),
            "type": doc["type"],
            "content": doc["content"],
            "status": doc["status"],
            "created_at": doc["created_at"].isoformat(),
        }
        notifications.append(notification)

    return notifications
