# Generated by Django 5.0.1 on 2024-03-10 18:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0033_transaction_transaction_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='Transaction_id',
            new_name='transaction_id',
        ),
    ]
