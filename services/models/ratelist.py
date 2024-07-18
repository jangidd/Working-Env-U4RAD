from django.db import models
from .personal_info import PersonalInformation

class RateList(models.Model):
    radiologist = models.ForeignKey(PersonalInformation, on_delete=models.CASCADE)
    mri1 = models.IntegerField(null=True, default=200, blank=True)
    mri2 = models.IntegerField(null=True, default=100, blank=True)
    mri3 = models.IntegerField(null=True, default=250, blank=True)
    mri4 = models.IntegerField(null=True, default=250, blank=True)
    mri5 = models.IntegerField(null=True, default=300, blank=True)
    mri6 = models.IntegerField(null=True, default=300, blank=True)
    ct1 = models.IntegerField(null=True, default=150, blank=True)
    ct2 = models.IntegerField(null=True, default=150, blank=True)
    ct3 = models.IntegerField(null=True, default=150, blank=True)
    ct4 = models.IntegerField(null=True, default=200, blank=True)
    ct5 = models.IntegerField(null=True, default=225, blank=True)
    ct6 = models.IntegerField(null=True, default=200, blank=True)
    ct7 = models.IntegerField(null=True, default=500, blank=True)
    xray1 = models.IntegerField(null=True, default=20, blank=True)
    xray2 = models.IntegerField(null=True, default=75, blank=True)
    status = models.CharField(max_length=50, default='No Status Yet', blank=True)

    def __str__(self):
        return f"{self.radiologist.first_name} {self.radiologist.last_name}"
