# Notification Service

## Objective

Build a system to send notifications to users.

## Features

1. **API Endpoints**:

   - Send a Notification (POST /notifications)
   - Get User Notifications (GET /users/{id}/notifications)
   - Health Check (GET /health)

2. **Notification Types**:

   - Email
   - SMS
   - In-app notifications

3. **Bonus Features**:
   - RabbitMQ queue for processing notifications
   - Retries for failed notifications (3 attempts with 2-second delay)
   - MongoDB for persistent storage

## Architecture

The notification service uses a queue-based architecture:

1. The API receives notification requests
2. Notifications are saved to MongoDB
3. Notifications are pushed to a RabbitMQ queue
4. A separate consumer process pulls messages from the queue and processes them
5. The appropriate notification service sends the notification based on type
6. Notification status is updated in the database

## Setup Instructions

### Prerequisites

- Python 3.8+
- MongoDB
- RabbitMQ

### Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure MongoDB and RabbitMQ are running locally:
   - MongoDB should be available at mongodb://localhost:27017/
   - RabbitMQ should be running on the default port (5672)

### Running the Service

1. Start the API server:

```bash
python app.py
```

2. In a separate terminal, start the consumer:

```bash
python consumer.py
```

## Testing the Notification Service

Here's how to test all aspects of the notification service:

### 1. Send an Email Notification

```bash
curl -X POST http://localhost:5000/notifications \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "type": "email", "content": "Test email notification"}'
```

PowerShell version:

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "email", "content": "Test email notification"}'
```

### 2. Send an SMS Notification

```bash
curl -X POST http://localhost:5000/notifications \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "type": "sms", "content": "Test SMS notification"}'
```

PowerShell version:

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "sms", "content": "Test SMS notification"}'
```

### 3. Send an In-App Notification

```bash
curl -X POST http://localhost:5000/notifications \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "type": "in-app", "content": "Test in-app notification"}'
```

PowerShell version:

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "in-app", "content": "Test in-app notification"}'
```

### 4. Retrieve User Notifications

```bash
curl http://localhost:5000/users/123/notifications
```

PowerShell version:

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/users/123/notifications'
```

### 5. Test Error Handling: Invalid Notification Type

```bash
curl -X POST http://localhost:5000/notifications \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "type": "invalid-type", "content": "This should fail"}'
```

PowerShell version:

```powershell
try { Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "invalid-type", "content": "This should fail"}' } catch { $_.Exception.Response.StatusCode }
```

### 6. Test Error Handling: Missing Required Field

```bash
curl -X POST http://localhost:5000/notifications \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "type": "email"}'
```

PowerShell version:

```powershell
try { Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "email"}' } catch { $_.Exception.Response.StatusCode }
```

### 7. Check Service Health

```bash
curl http://localhost:5000/health
```

PowerShell version:

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/health'
```

- MongoDB
- RabbitMQ

### Installation

1. Clone the repository:

   ```
   git clone <repository-url>
   cd notification_service
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Make sure MongoDB is running:

   - Install MongoDB: https://www.mongodb.com/docs/manual/installation/
   - Start MongoDB service

4. Make sure RabbitMQ is running:
   - Install RabbitMQ: https://www.rabbitmq.com/download.html
   - Start RabbitMQ service

### Running the Service

1. Start the API server:

   ```
   python app.py
   ```

2. In a separate terminal, start the notification consumer:
   ```
   python consumer.py
   ```

## API Documentation

### 1. Send a Notification

**Endpoint:** `POST /notifications`

**Request Body:**

```json
{
  "user_id": 123,
  "type": "email",
  "content": "This is a test notification"
}
```

**Supported notification types:**

- `email`
- `sms`
- `in-app`

**Response (Success):**

```json
{
  "message": "Notification sent successfully",
  "notification_id": "60f8f1b3c2d7a8f9e1d2c3b4"
}
```

**Response (Error):**

```json
{
  "error": "type must be one of: email, sms, in-app"
}
```

### 2. Get User Notifications

**Endpoint:** `GET /users/{user_id}/notifications`

**Response:**

```json
{
  "user_id": 123,
  "notifications": [
    {
      "id": "60f8f1b3c2d7a8f9e1d2c3b4",
      "type": "email",
      "content": "This is a test notification",
      "status": "delivered",
      "created_at": "2023-07-22T15:30:45.123456"
    }
  ]
}
```

### 3. Health Check

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "ok"
}
```

## Assumptions

1. MongoDB and RabbitMQ are running on localhost with default ports.
2. Email, SMS, and in-app notification services are mocked for demonstration purposes.
3. There is no user authentication/authorization implemented.
4. Notification delivery logic is simulated rather than integrated with actual email/SMS providers.

## Future Improvements

1. Add authentication middleware
2. Implement actual notification delivery services
3. Add notification templates
4. Add unit and integration tests
5. Add rate limiting for notification senders
6. Add API documentation with Swagger/OpenAPI
7. Add environment variable configuration
8. Containerize the application with Docker

## Deployment Guide

This service is containerized using Docker and can be deployed in various environments.

### Environment Variables

Configure the service by setting environment variables. Copy `.env.template` to `.env` and modify as needed:

```bash
cp .env.template .env
```

Key environment variables:

- `ENVIRONMENT`: Set to 'development', 'testing', or 'production'
- `MONGODB_URI`: URI for MongoDB connection
- `RABBITMQ_HOST`: RabbitMQ host
- `API_PORT`: Port for the API to listen on (default: 5000)

### Deploying with Docker

#### Single Service with Docker

1. Build the Docker image:

```bash
docker build -t notification-service .
```

2. Run the API:

```bash
docker run -p 5000:5000 --name notification-api --env-file .env notification-service python app.py
```

3. Run the consumer:

```bash
docker run --name notification-consumer --env-file .env notification-service python consumer.py
```

#### Full Stack with Docker Compose

```bash
docker-compose up -d
```

This will start:

- API service on port 5000
- Consumer service processing messages from RabbitMQ
- MongoDB database with persistent storage
- RabbitMQ server with management interface on port 15672

### Scaling

The notification consumer can be horizontally scaled to handle increased load:

```bash
docker-compose up -d --scale consumer=3
```

### Health Checks

The API provides a health endpoint at `/health` that returns status information.

### Monitoring

The RabbitMQ management interface is available at http://localhost:15672 when using Docker Compose.
Default credentials: guest/guest

## Running Tests

Run the test suite:

```bash
python test_notification_service.py
```

Run with verbose output:

```bash
python test_notification_service.py -v
```
