# Generated by Django 2.2.16 on 2023-03-21 09:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20230321_1428'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='groups',
        ),
    ]
