from django.db import models
from .models import Service
from django.contrib.auth.models import User

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, default=1)
    quantity = models.PositiveIntegerField(default=0)
    casecount = models.PositiveIntegerField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Cart Item: {self.service.service_name} (Quantity: {self.quantity})"

class UploadFile(models.Model):
    cart = models.ForeignKey(Cart, related_name='uploads', on_delete=models.CASCADE, default=None, null=True, blank=True)
    file = models.FileField(upload_to='uploads/')
    upload_time = models.DateTimeField(auto_now_add=True)
