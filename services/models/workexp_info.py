from django.db import models
from .personal_info import PersonalInformation

class ExperienceDetails(models.Model):
    exinstitution1 = models.CharField(max_length=30, null=True, default=None, blank=True)
    exstdate1 = models.DateField(null=True, default=None, blank=True)
    exenddate1 = models.DateField(null=True, default=None, blank=True)
    exinstitution2 = models.CharField(max_length=30, null=True, default=None, blank=True)
    exstdate2 = models.DateField(null=True, default=None, blank=True)
    exenddate2 = models.DateField(null=True, default=None, blank=True)
    exinstitution3 = models.CharField(max_length=30, null=True, default=None, blank=True)
    exstdate3 = models.DateField(null=True, default=None, blank=True)
    exenddate3 = models.DateField(null=True, default=None, blank=True)
    personal_information = models.ForeignKey(
        PersonalInformation,
        on_delete=models.CASCADE,
        default=None  # Replace with the default value you want to use
    )

    def __str__(self):
        return self.personal_information.first_name + self.personal_information.last_name