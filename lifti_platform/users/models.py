from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime
import requests

class MonthYearField(models.DateField):
    description = "A field to store only month and year"

    def get_prep_value(self, value):
        if value is not None:
            return value.replace(day=1)
        return value

    def from_db_value(self, value, expression, connection):
        return value

    def to_python(self, value):
        return value

class Cooperative(models.Model): 
    cooperative_name = models.CharField(max_length=50)
    cooperative_address = models.CharField(max_length=100)
    cooperative_device_price = models.DecimalField(max_digits=10, decimal_places=2, default=00.10)
    def __str__(self):
        return self.cooperative_name
    
class CooperativeExpense(models.Model):
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name='expenses')
    date = MonthYearField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)


class Client(AbstractUser):
    mobile_number = models.CharField(max_length=15)
    apartment_number = models.CharField(max_length=20)
    cooperative_id = models.CharField(max_length=50)
    password_changed = models.BooleanField(default=False)
    allowed_cooperatives = models.ManyToManyField(Cooperative, related_name='allowed_clients', blank=True)
    head = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='client_users',
        blank=True,
        help_text='The groups this client belongs to. A client will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='client_users',
        blank=True,
        help_text='Specific permissions for this client.',
        verbose_name='user permissions',
    )
    def save(self, *args, **kwargs):
        if self.mobile_number and not self.sms_sent:
            # Logic to send SMS
            api_key = "9be3300ffa6688e040b6981d170d153b"  # Use your actual API key
            message = SmsText.objects.get(id=1).text
            sms_url = "https://sender.ge/api/send.php"
            params = {
                "apikey": api_key,
                "smsno": 2, 
                "destination": self.mobile_number,
                "content": message,
            }

            try:
                response = requests.get(sms_url, params=params)
                response.raise_for_status()
                self.sms_sent = True  # Mark SMS as sent
            except requests.RequestException as e:
                # Log error or handle exception
                print(e)

        super(Client, self).save(*args, **kwargs)

    def __str__(self):
        return self.username



class Card(models.Model): 
    card_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='cards')
    temp = models.BooleanField(default=False)
    for_mobile = models.CharField(max_length=15, default='null')
    life_hours = models.CharField(max_length=15, default='null')
    created_at = models.DateTimeField(default=datetime.now)
    def __str__(self): 
        return self.card_number

class Device(models.Model): 
    device_name = models.CharField(max_length=50)
    device_ip = models.CharField(max_length=50)
    device_port = models.IntegerField()
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE)

class DeviceEvent(models.Model): 
    device_id = models.IntegerField()
    user = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='device_events', default=2)
    timestamp = models.CharField(max_length=250)
    pin = models.IntegerField()
    card = models.CharField(max_length=20)
    event_type = models.IntegerField()
    verify_mode = models.CharField
    processed = models.BooleanField(default=False)
    payed = models.CharField(max_length=20, default="0")

class Balance(models.Model):
    user_balance = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='balance')
    user_balance_delta = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class SubscriptionType(models.Model): 
    subscription_name = models.CharField(max_length=50, default='აბონემენტი')
    subscription_days = models.IntegerField()
    subscription_price = models.DecimalField(max_digits=10, decimal_places=2)
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name='subscription_types')
    def __str__(self): 
        return self.subscription_name
    

class Subscription(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    cooperative = models.ForeignKey(Cooperative, on_delete=models.CASCADE, related_name='subscriptions')

class SubsObserverLog(models.Model): 
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='subscription_logs')
    card_number = models.CharField(max_length=20)
    operation_to_do = models.CharField(max_length=50)
    processed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)


class BalanceObserverLog(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='balance_logs')
    card_number = models.CharField(max_length=20)
    operation_to_do = models.CharField(max_length=50)
    processed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class CardObserverLog(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='card_logs')
    card_number = models.CharField(max_length=20)
    operation_to_do = models.CharField(max_length=50)
    processed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class AllowedCoopObserver(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='allowed_cooperative_logs')
    cooperative = models.CharField(max_length=50)
    operation_to_do = models.CharField(max_length=50)
    processed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class Transaction(models.Model):
    user = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status_choices = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=200, default="transaction")

class SmsText(models.Model):
    case = models.CharField(max_length=50)
    text = models.CharField(max_length=250)