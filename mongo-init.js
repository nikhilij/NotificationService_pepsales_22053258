// MongoDB initialization script
// Creates database user and indexes for the notification service

db = db.getSiblingDB("admin");
db.auth(process.env.MONGO_INITDB_ROOT_USERNAME, process.env.MONGO_INITDB_ROOT_PASSWORD);

db = db.getSiblingDB("notification_service");

// Create a user for the notification service
db.createUser({
  user: process.env.MONGO_USER || "notification_service_user",
  pwd: process.env.MONGO_PASSWORD || "password",
  roles: [{ role: "readWrite", db: "notification_service" }],
});

// Create collection for notifications
db.createCollection("notifications");

// Create indexes
db.notifications.createIndex({ user_id: 1 });
db.notifications.createIndex({ created_at: -1 });
db.notifications.createIndex({ status: 1 });

print("MongoDB initialization completed successfully!");
