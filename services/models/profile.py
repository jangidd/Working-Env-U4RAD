# models.py

from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=100, blank=True)
    organization = models.CharField(max_length=100, blank=True)

class UploadFile(models.Model):
    profile = models.ForeignKey(Profile, related_name='uploads', on_delete=models.CASCADE, default=None, null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    upload_time = models.DateTimeField(auto_now_add=True)