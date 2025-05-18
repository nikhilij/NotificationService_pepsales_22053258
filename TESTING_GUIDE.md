# Complete Testing Guide for Notification Service

This guide provides step-by-step instructions for testing your notification service. Follow each step to verify that all components of your system are working correctly.

## Prerequisites

Before testing, ensure:

1. MongoDB is running on localhost:27017
2. RabbitMQ is running on default port (5672)
3. Both the API server and consumer are running in separate terminals:
   - Terminal 1: `python app.py`
   - Terminal 2: `python consumer.py`

## Test Scenarios

### 1. Basic Functionality Tests

#### 1.1 Send Email Notification

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "email", "content": "Test email notification"}'
```

Expected result:

- Status code: 200
- Response contains: "message": "Notification sent successfully"
- Response includes a notification_id
- The consumer log should show a message about sending an email notification
- The notification should be saved to the database with "status": "delivered"

#### 1.2 Send SMS Notification

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "sms", "content": "Test SMS notification"}'
```

Expected result:

- Same pattern as with email notification
- The consumer log shows a message about sending an SMS

#### 1.3 Send In-App Notification

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "in-app", "content": "Test in-app notification"}'
```

Expected result:

- Same pattern as with other notification types
- The consumer log shows a message about sending an in-app notification

#### 1.4 Retrieve User Notifications

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/users/123/notifications'
```

Expected result:

- Status code: 200
- Response contains an array of notifications for user 123
- Each notification should include id, type, content, status, and created_at
- Notifications should be sorted with newest first

### 2. Error Handling Tests

#### 2.1 Invalid Notification Type

```powershell
try {
    Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "invalid-type", "content": "This should fail"}'
} catch {
    $_.Exception.Response.StatusCode
    $response = $_.Exception.Response
    $responseStream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($responseStream)
    $reader.BaseStream.Position = 0
    $reader.ReadToEnd()
}
```

Expected result:

- Status code: 400 (Bad Request)
- Response contains error message about invalid type

#### 2.2 Missing Required Field (Content)

```powershell
try {
    Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "email"}'
} catch {
    $_.Exception.Response.StatusCode
    $response = $_.Exception.Response
    $responseStream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($responseStream)
    $reader.BaseStream.Position = 0
    $reader.ReadToEnd()
}
```

Expected result:

- Status code: 400 (Bad Request)
- Response contains error message about missing content field

#### 2.3 Missing Required Field (User ID)

```powershell
try {
    Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"type": "email", "content": "Missing user ID"}'
} catch {
    $_.Exception.Response.StatusCode
    $response = $_.Exception.Response
    $responseStream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($responseStream)
    $reader.BaseStream.Position = 0
    $reader.ReadToEnd()
}
```

Expected result:

- Status code: 400 (Bad Request)
- Response contains error message about missing user_id field

### 3. System Health Test

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/health'
```

Expected result:

- Status code: 200
- Response contains: "status": "ok"

### 4. Integration Tests

#### 4.1 Multiple Notifications Test

Send multiple notifications of different types in sequence and then check they are all available:

```powershell
# Send 3 different notifications
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 456, "type": "email", "content": "Multi-test email"}'
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 456, "type": "sms", "content": "Multi-test SMS"}'
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 456, "type": "in-app", "content": "Multi-test in-app"}'

# Check they all arrived
Invoke-RestMethod -Uri 'http://localhost:5000/users/456/notifications' | ConvertTo-Json -Depth 4
```

Expected result:

- All 3 notifications are returned for user 456
- Each notification has the correct type and content

#### 4.2 High Volume Test

```powershell
# Send 10 notifications in quick succession
1..10 | ForEach-Object {
    Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body ('{"user_id": 789, "type": "email", "content": "Bulk test ' + $_ + '"}')
}

# Check they all arrived
Invoke-RestMethod -Uri 'http://localhost:5000/users/789/notifications' | ConvertTo-Json -Depth 4
```

Expected result:

- All 10 notifications are processed and saved
- The consumer handles the load without errors

## Troubleshooting

If tests fail, check:

1. Are MongoDB and RabbitMQ running?
2. Are both the API server (app.py) and consumer (consumer.py) running?
3. Check logs for any errors
4. Verify connection strings for both MongoDB and RabbitMQ

## Database Verification

To directly verify that notifications are being saved to MongoDB:

1. Open MongoDB shell:

   ```
   mongosh
   ```

2. Switch to your database:

   ```
   use notification_service
   ```

3. Query notifications collection:
   ```
   db.notifications.find().sort({created_at: -1}).pretty()
   ```

## Automated Testing

### Running the Test Suite

The project includes a comprehensive test suite that verifies all components. To run all tests:

```powershell
python test_notification_service.py
```

For more detailed test output:

```powershell
python test_notification_service.py -v
```

### Test Coverage

To generate test coverage reports:

1. Install coverage tool (if not already installed):

```powershell
pip install coverage
```

2. Run tests with coverage:

```powershell
coverage run --source=. test_notification_service.py
```

3. Generate HTML report:

```powershell
coverage html
```

4. Open the report in your browser:

```powershell
Start-Process .\htmlcov\index.html
```

### Docker Deployment Testing

To test the Docker deployment:

1. Build and start all services:

```powershell
docker-compose up --build -d
```

2. Check if all services are running:

```powershell
docker-compose ps
```

3. Test the API endpoint:

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/health'
```

4. Send a test notification:

```powershell
Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body '{"user_id": 123, "type": "email", "content": "Docker test notification"}'
```

5. Check logs from the consumer service:

```powershell
docker-compose logs consumer
```

6. Access the RabbitMQ management interface at http://localhost:15672 using guest/guest login.

7. Stop all services when done:

```powershell
docker-compose down
```

### Load Testing

For basic load testing:

```powershell
# Send 50 notifications in parallel
1..50 | ForEach-Object -Parallel {
    Invoke-RestMethod -Uri 'http://localhost:5000/notifications' -Method Post -ContentType 'application/json' -Body ('{"user_id": 999, "type": "email", "content": "Load test ' + $_ + '"}')
} -ThrottleLimit 10
```

For more advanced load testing, consider using tools like Apache JMeter or k6.
