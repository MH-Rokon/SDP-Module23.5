# Generated by Django 4.2.4 on 2024-01-03 21:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0004_transaction_aceecess_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='aceecess',
        ),
    ]
