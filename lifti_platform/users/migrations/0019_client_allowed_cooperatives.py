# Generated by Django 5.0.1 on 2024-02-05 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_cooperative_cooperative_device_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='allowed_cooperatives',
            field=models.ManyToManyField(blank=True, related_name='allowed_clients', to='users.cooperative'),
        ),
    ]
