"""Configuration management for the notification service."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Environment settings
ENV = os.getenv("ENVIRONMENT", "development")  # development, testing, production

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "notification_service")
if ENV == "testing":
    MONGODB_DATABASE = "notification_service_test"

# RabbitMQ settings
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "notifications")
RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/",
)

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "5000"))
DEBUG = ENV != "production"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")
