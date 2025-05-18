import json
import logging
import warnings

# Silence the warnings we don't care about
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Just the important logs
logging.basicConfig(
    level=logging.WARNING,  # Only log warnings and errors
    format="%(levelname)s: %(message)s"  # No timestamps or extra fluff
)
logger = logging.getLogger(__name__)


class NotificationService:
    """The parent of all notification types - like a blueprint"""

    def send(self, user_id, content):
        """
        Gets your message to where it needs to go
        
        Just needs:
        - who's getting it (user_id)
        - what we're telling them (content)
        
        Lets you know if it worked or not
        """
        raise NotImplementedError("Subclasses must implement this method")


class EmailNotificationService(NotificationService):
    """The email sender - gets stuff to your inbox"""

    def send(self, user_id, content):
        # This would hook into SendGrid or something in real life
        logger.info(f"Shooting an email to user {user_id}: {content}")
        # Let's pretend it worked
        return True


class SMSNotificationService(NotificationService):
    """The text messenger - pings your phone"""

    def send(self, user_id, content):
        # Would connect to Twilio in the real world
        logger.info(f"Texting user {user_id}: {content}")
        # All good on our end!
        return True


class InAppNotificationService(NotificationService):
    """The popup maker - catches you in the app"""

    def send(self, user_id, content):
        # Would be websockets in the real deal
        logger.info(f"Popping up for user {user_id}: {content}")
        # Looks like it worked!
        return True


def get_notification_service(notification_type):
    """
    The service dispatcher - figures out how to send your message
    
    Tells you which sender to use based on what kind of notification
    you want to send (email, text, or in-app pop-up)
    
    Will complain if you try something weird we don't support
    """
    notification_services = {
        "email": EmailNotificationService(),
        "sms": SMSNotificationService(),
        "in-app": InAppNotificationService(),
    }

    if notification_type not in notification_services:
        raise ValueError(f"Unsupported notification type: {notification_type}")

    return notification_services[notification_type]
