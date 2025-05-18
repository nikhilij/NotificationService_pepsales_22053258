import unittest
import json
import os
from unittest.mock import patch, MagicMock
from pymongo import MongoClient
import sys
import time
from datetime import datetime
from bson.objectid import ObjectId

# Add the current directory to the path so that we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import (
    save_notification,
    get_user_notifications,
    update_notification_status,
)
from notification_services import (
    get_notification_service,
    EmailNotificationService,
    SMSNotificationService,
    InAppNotificationService,
)
from consumer import process_notification


class TestNotificationService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test database before running tests"""
        cls.app = app.test_client()
        # Create a test MongoDB client
        cls.mongo_client = MongoClient("mongodb://localhost:27017/")
        cls.db = cls.mongo_client["notification_service_test"]
        cls.notifications_collection = cls.db["notifications"]

    def setUp(self):
        """Set up test case before each test"""
        # Clear the test collection before each test
        self.notifications_collection.delete_many({})

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run"""
        # Drop the test database
        cls.mongo_client.drop_database("notification_service_test")

    @patch("database.notifications_collection")
    def test_save_notification(self, mock_collection):
        """Test saving a notification to the database"""
        # Setup
        mock_collection.insert_one.return_value.inserted_id = ObjectId(
            "60f8f1b3c2d7a8f9e1d2c3b4"
        )

        # Execute
        result = save_notification(123, "email", "Test content")

        # Assert
        self.assertEqual(result, "60f8f1b3c2d7a8f9e1d2c3b4")
        mock_collection.insert_one.assert_called_once()
        args = mock_collection.insert_one.call_args[0][0]
        self.assertEqual(args["user_id"], 123)
        self.assertEqual(args["type"], "email")
        self.assertEqual(args["content"], "Test content")
        self.assertEqual(args["status"], "pending")
        self.assertIsNotNone(args["created_at"])

    @patch("database.notifications_collection")
    def test_get_user_notifications(self, mock_collection):
        """Test retrieving user notifications from the database"""
        # Setup
        created_time = datetime.now()
        mock_notification = {
            "_id": ObjectId("60f8f1b3c2d7a8f9e1d2c3b4"),
            "user_id": 123,
            "type": "email",
            "content": "Test content",
            "status": "delivered",
            "created_at": created_time,
        }

        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = [mock_notification]
        mock_collection.find.return_value.sort.return_value = mock_cursor

        # Execute
        result = get_user_notifications(123)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "60f8f1b3c2d7a8f9e1d2c3b4")
        self.assertEqual(result[0]["type"], "email")
        self.assertEqual(result[0]["content"], "Test content")
        self.assertEqual(result[0]["status"], "delivered")
        self.assertEqual(result[0]["created_at"], created_time.isoformat())

    @patch("database.notifications_collection")
    def test_update_notification_status(self, mock_collection):
        """Test updating notification status"""
        # Setup
        notification_id = "60f8f1b3c2d7a8f9e1d2c3b4"

        # Execute
        update_notification_status(notification_id, "delivered")

        # Assert
        mock_collection.update_one.assert_called_once_with(
            {"_id": ObjectId(notification_id)}, {"$set": {"status": "delivered"}}
        )

    def test_get_notification_service(self):
        """Test notification service factory method"""
        # Test valid notification types
        email_service = get_notification_service("email")
        sms_service = get_notification_service("sms")
        in_app_service = get_notification_service("in-app")

        self.assertIsInstance(email_service, EmailNotificationService)
        self.assertIsInstance(sms_service, SMSNotificationService)
        self.assertIsInstance(in_app_service, InAppNotificationService)

        # Test invalid notification type
        with self.assertRaises(ValueError):
            get_notification_service("invalid")

    @patch("notification_services.EmailNotificationService.send")
    def test_email_notification_service(self, mock_send):
        """Test email notification service"""
        # Setup
        mock_send.return_value = True
        service = EmailNotificationService()

        # Execute
        result = service.send(123, "Test email content")

        # Assert
        self.assertTrue(result)
        mock_send.assert_called_once_with(123, "Test email content")

    @patch("notification_services.SMSNotificationService.send")
    def test_sms_notification_service(self, mock_send):
        """Test SMS notification service"""
        # Setup
        mock_send.return_value = True
        service = SMSNotificationService()

        # Execute
        result = service.send(123, "Test SMS content")

        # Assert
        self.assertTrue(result)
        mock_send.assert_called_once_with(123, "Test SMS content")

    @patch("notification_services.InAppNotificationService.send")
    def test_in_app_notification_service(self, mock_send):
        """Test in-app notification service"""
        # Setup
        mock_send.return_value = True
        service = InAppNotificationService()

        # Execute
        result = service.send(123, "Test in-app content")

        # Assert
        self.assertTrue(result)
        mock_send.assert_called_once_with(123, "Test in-app content")

    @patch("consumer.update_notification_status")
    @patch("consumer.get_notification_service")
    def test_process_notification_success(self, mock_get_service, mock_update_status):
        """Test successful notification processing"""
        # Setup
        mock_service = MagicMock()
        mock_service.send.return_value = True
        mock_get_service.return_value = mock_service

        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"

        notification_data = {
            "id": "60f8f1b3c2d7a8f9e1d2c3b4",
            "user_id": 123,
            "type": "email",
            "content": "Test content",
        }

        body = json.dumps(notification_data).encode("utf-8")

        # Execute
        process_notification(mock_channel, mock_method, None, body)

        # Assert
        mock_get_service.assert_called_once_with("email")
        mock_service.send.assert_called_once_with(123, "Test content")
        mock_update_status.assert_called_once_with(
            "60f8f1b3c2d7a8f9e1d2c3b4", "delivered"
        )
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")

    @patch("consumer.update_notification_status")
    @patch("consumer.get_notification_service")
    def test_process_notification_failure(self, mock_get_service, mock_update_status):
        """Test failed notification processing"""
        # Setup
        mock_service = MagicMock()
        mock_service.send.return_value = False
        mock_get_service.return_value = mock_service

        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"

        notification_data = {
            "id": "60f8f1b3c2d7a8f9e1d2c3b4",
            "user_id": 123,
            "type": "email",
            "content": "Test content",
        }

        body = json.dumps(notification_data).encode("utf-8")

        # Execute
        process_notification(mock_channel, mock_method, None, body)

        # Assert
        mock_get_service.assert_called_once_with("email")
        mock_service.send.assert_called_once_with(123, "Test content")
        mock_update_status.assert_called_once_with("60f8f1b3c2d7a8f9e1d2c3b4", "failed")
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")

    @patch("consumer.get_notification_service")
    @patch("consumer.update_notification_status")
    def test_process_notification(self, mock_update_status, mock_get_service):
        """Test process_notification function"""
        # Setup
        mock_service = MagicMock()
        mock_service.send.return_value = True
        mock_get_service.return_value = mock_service

        mock_channel = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = "test_tag"
        mock_properties = None

        notification_data = {
            "id": "60f8f1b3c2d7a8f9e1d2c3b4",
            "user_id": 123,
            "type": "email",
            "content": "Test content",
        }
        body = json.dumps(notification_data).encode("utf-8")

        # Execute
        process_notification(mock_channel, mock_method, mock_properties, body)

        # Assert
        mock_get_service.assert_called_once_with("email")
        mock_service.send.assert_called_once_with(123, "Test content")
        mock_update_status.assert_called_once_with(
            "60f8f1b3c2d7a8f9e1d2c3b4", "delivered"
        )
        mock_channel.basic_ack.assert_called_once_with(delivery_tag="test_tag")

    def test_send_notification_api(self):
        """Test the API endpoint for sending notifications"""
        # Setup
        with patch("app.send_to_queue") as mock_send_to_queue, patch(
            "app.save_notification"
        ) as mock_save_notification:

            mock_save_notification.return_value = "60f8f1b3c2d7a8f9e1d2c3b4"

            # Execute
            response = self.app.post(
                "/notifications",
                data=json.dumps(
                    {"user_id": 123, "type": "email", "content": "Test content"}
                ),
                content_type="application/json",
            )

            # Assert
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.data)
            self.assertEqual(response_data["message"], "Notification sent successfully")
            self.assertEqual(
                response_data["notification_id"], "60f8f1b3c2d7a8f9e1d2c3b4"
            )

            mock_save_notification.assert_called_once_with(123, "email", "Test content")
            mock_send_to_queue.assert_called_once()

    def test_get_user_notifications_api(self):
        """Test the API endpoint for retrieving user notifications"""
        # Setup
        with patch("app.get_user_notifications") as mock_get_notifications:
            mock_get_notifications.return_value = [
                {
                    "id": "60f8f1b3c2d7a8f9e1d2c3b4",
                    "type": "email",
                    "content": "Test content",
                    "status": "delivered",
                    "created_at": "2023-07-22T15:30:45.123456",
                }
            ]

            # Execute
            response = self.app.get("/users/123/notifications")

            # Assert
            self.assertEqual(response.status_code, 200)
            response_data = json.loads(response.data)
            self.assertEqual(response_data["user_id"], 123)
            self.assertEqual(len(response_data["notifications"]), 1)
            self.assertEqual(
                response_data["notifications"][0]["id"], "60f8f1b3c2d7a8f9e1d2c3b4"
            )

            mock_get_notifications.assert_called_once_with(123)

    def test_health_check_api(self):
        """Test the health check API endpoint"""
        # Execute
        response = self.app.get("/health")

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["status"], "ok")


if __name__ == "__main__":
    unittest.main()
