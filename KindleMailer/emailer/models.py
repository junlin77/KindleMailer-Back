from django.db import models

class UserProfile(models.Model):
    google_user_id = models.CharField(max_length=255, unique=True)
    kindle_email = models.EmailField(max_length=255, unique=True)
