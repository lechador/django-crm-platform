# Generated by Django 5.0.1 on 2024-04-03 00:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0048_allowedcoopobserver'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscription',
            name='price',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=10),
        ),
    ]
