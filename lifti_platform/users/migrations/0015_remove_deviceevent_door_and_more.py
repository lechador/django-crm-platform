# Generated by Django 5.0.1 on 2024-01-30 11:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_deviceevent_processed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deviceevent',
            name='door',
        ),
        migrations.RemoveField(
            model_name='deviceevent',
            name='entry_exit',
        ),
    ]
