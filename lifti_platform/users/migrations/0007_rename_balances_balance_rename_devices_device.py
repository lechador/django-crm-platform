# Generated by Django 5.0.1 on 2024-01-29 12:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_rename_cards_card'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Balances',
            new_name='Balance',
        ),
        migrations.RenameModel(
            old_name='Devices',
            new_name='Device',
        ),
    ]
