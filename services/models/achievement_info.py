from django.db import models
from .personal_info import PersonalInformation

class AchievementDetails(models.Model):
    award1 = models.CharField(max_length=30, null=True, default=None, blank=True)
    awarddate1 = models.DateField(null=True, default=None, blank=True)
    award2 = models.CharField(max_length=30, null=True, default=None, blank=True)
    awarddate2 = models.DateField(null=True, default=None, blank=True)
    publishlink = models.CharField(max_length=30, null=True, default=None, blank=True)
    personal_information = models.ForeignKey(
        PersonalInformation,
        on_delete=models.CASCADE,
        default=None  # Replace with the default value you want to use
    )

    def __str__(self):
        return self.personal_information.first_name + self.personal_information.last_name