# Generated by Django 5.0.1 on 2024-01-29 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_subscriptiontype_subscription_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.1, max_digits=10),
        ),
    ]
