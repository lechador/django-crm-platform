from django.core.management.base import BaseCommand
from datetime import timedelta, datetime
from users.models import Card, SubsObserverLog

class Command(BaseCommand):
    help = 'Deletes expired temporary cards'

    def handle(self, *args, **options):
        # Get temporary cards with life_hours set
        cards_with_life_hours = Card.objects.filter(temp=True, life_hours__isnull=False)

        # Calculate expiry datetime for each card
        for card in cards_with_life_hours:
            expiry_datetime = card.created_at + timedelta(hours=card.life_hours)

            # If the expiry datetime has passed, create log entry and delete the card
            if datetime.now() > expiry_datetime:
                SubsObserverLog.objects.create(card_number=card.card_number, operation_to_do="remove card", processed=False, user_id=card.user_id)
                card.delete()
