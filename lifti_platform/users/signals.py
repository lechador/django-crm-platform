from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Client, Balance, Card, CardObserverLog, Cooperative, AllowedCoopObserver
from django.db.models.signals import m2m_changed
from datetime import datetime

@receiver(post_save, sender=Client)
def create_user_balance(sender, instance, created, **kwargs):
    """
    Signal receiver function to create a balance entry for a newly created user.
    """
    if created:
        Balance.objects.create(user=instance, user_balance=0)


@receiver(post_delete, sender=Card)
def create_balance_observer_log(sender, instance, **kwargs):
    CardObserverLog.objects.create(
        user=instance.user,
        card_number=instance.card_number,
        operation_to_do='remove card'
    )

@receiver(post_save, sender=Card)
def create_balance_observer_log(sender, instance, **kwargs):
    CardObserverLog.objects.create(
        user=instance.user,
        card_number=instance.card_number,
        operation_to_do='add card'
    )


@receiver(m2m_changed, sender=Client.allowed_cooperatives.through)
def handle_allowed_cooperatives_change(sender, instance, action, **kwargs):
    if action == 'post_add':
        for cooperative_id in kwargs['pk_set']:
            AllowedCoopObserver.objects.create(user=instance, cooperative=cooperative_id, operation_to_do='add card')
    elif action == 'post_remove':
        for cooperative_id in kwargs['pk_set']:
            AllowedCoopObserver.objects.create(user=instance, cooperative=cooperative_id, operation_to_do='remove card')