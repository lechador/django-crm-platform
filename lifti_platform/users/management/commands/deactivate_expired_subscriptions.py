from django.core.management.base import BaseCommand
from datetime import datetime
from users.models import Subscription
import requests

class Command(BaseCommand):
    help = 'Updates expired subscriptions'

    def handle(self, *args, **options):
        now = datetime.now()
        expired_subscriptions = Subscription.objects.filter(end_date__lt=now, is_active=True)

        for subscription in expired_subscriptions:
            subscription.is_active = False
            subscription.save()

            # Send SMS to the user's mobile number
            api_key = "9be3300ffa6688e040b6981d170d153b"  # Use your actual API key
            message = "Your subscription has been deactivated"  # Modify message as needed
            sms_url = "https://sender.ge/api/send.php"
            params = {
                "apikey": api_key,
                "smsno": 2, 
                "destination": subscription.user.mobile_number,  # Get the user's mobile number from the subscription
                "content": message,
            }
            try:
                response = requests.get(sms_url, params=params)
                response.raise_for_status()
                self.stdout.write(self.style.SUCCESS(f'Successfully sent SMS to {subscription.user.mobile_number}'))
            except requests.RequestException as e:
                self.stderr.write(f'Failed to send SMS to {subscription.user.mobile_number}: {e}')

        self.stdout.write(self.style.SUCCESS(f'Successfully deactivated {expired_subscriptions.count()} expired subscriptions.'))
