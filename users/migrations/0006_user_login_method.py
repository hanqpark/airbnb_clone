# Generated by Django 2.2.5 on 2021-01-27 01:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20210126_1135'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='login_method',
            field=models.CharField(choices=[('en', 'English'), ('kr', 'Korean'), ('jp', 'Japanese')], default='email', max_length=50),
        ),
    ]
