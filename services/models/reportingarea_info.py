from django.db import models
from .personal_info import PersonalInformation

class ReportingAreaDetails(models.Model):
    mriopt = models.CharField(max_length=50)
    mriothers = models.CharField(max_length=100)
    ctopt = models.CharField(max_length=50)
    ctothers = models.CharField(max_length=100)
    xray = models.BooleanField()
    others = models.BooleanField()
    otherText = models.CharField(max_length=100,null=True, default=None, blank=True)
    personal_information = models.ForeignKey(
        PersonalInformation,
        on_delete=models.CASCADE,
        default=None  # Replace with the default value you want to use
    )

    def __str__(self):
        return self.personal_information.first_name + self.personal_information.last_name