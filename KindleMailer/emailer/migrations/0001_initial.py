# Generated by Django 4.2.3 on 2023-08-05 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('google_user_id', models.CharField(max_length=255, unique=True)),
                ('kindle_email', models.EmailField(max_length=255, unique=True)),
            ],
        ),
    ]
