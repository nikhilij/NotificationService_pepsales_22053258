#!/bin/bash
# Quick development setup script for the notification service

# Create and activate virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Determine OS and activate virtual environment accordingly
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check MongoDB connection
echo "Checking MongoDB connection..."
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017/'); print('MongoDB connection successful' if client.server_info() else 'MongoDB connection failed')" || echo "Failed to connect to MongoDB. Please make sure MongoDB is running."

# Check RabbitMQ connection
echo "Checking RabbitMQ connection..."
python -c "import pika; connection = pika.BlockingConnection(pika.ConnectionParameters('localhost')); connection.channel(); print('RabbitMQ connection successful'); connection.close()" || echo "Failed to connect to RabbitMQ. Please make sure RabbitMQ is running."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo ".env file created. You may want to review and edit it."
fi

echo ""
echo "Setup complete! You can now start the application with:"
echo "- In one terminal: python app.py"
echo "- In another terminal: python consumer.py"
echo ""
echo "Run tests with: python test_notification_service.py"
