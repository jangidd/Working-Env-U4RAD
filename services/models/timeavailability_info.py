from django.db import models
from .personal_info import PersonalInformation

class AvailabilityDetails(models.Model):
    monday = models.BooleanField()
    tuesday = models.BooleanField()
    wednesday = models.BooleanField()
    thursday = models.BooleanField()
    friday = models.BooleanField()
    saturday = models.BooleanField()
    sunday = models.BooleanField()
    starttime1 = models.CharField(max_length=100, null=True, default="Individual", blank=True)
    endtime1 = models.CharField(max_length=100,null=True, default="Individual", blank=True)
    starttime2 = models.CharField(max_length=100,null=True, default="Individual", blank=True)
    endtime2 = models.CharField(max_length=100,null=True, default="Individual", blank=True)
    starttime3 = models.CharField(max_length=100,null=True, default="Individual", blank=True)
    endtime3 = models.CharField(max_length=100,null=True, default="Individual", blank=True)
    starttime4 = models.CharField(max_length=100,null=True, default="Individual", blank=True)
    endtime4 = models.CharField(max_length=100,null=True, default="Individual", blank=True)


    personal_information = models.ForeignKey(
        PersonalInformation,
        on_delete=models.CASCADE,
        default=None  # Replace with the default value you want to use
    )

    def __str__(self):
        return self.personal_information.first_name + self.personal_information.last_name