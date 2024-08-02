from django.db import models
from .personal_info import PersonalInformation

class EducationalDetails(models.Model):
    tenthname = models.CharField(max_length=30)
    tenthgrade = models.CharField(max_length=10)
    tenthpsyr = models.DateField()
    tenthcertificate = models.FileField(upload_to='uploads/')
    twelthname = models.CharField(max_length=30)
    twelthgrade = models.CharField(max_length=10)
    twelthpsyr = models.DateField()
    twelthcertificate = models.FileField(upload_to='uploads/')
    mbbsinstitution = models.CharField(max_length=25)
    mbbsgrade = models.CharField(max_length=10)
    mbbspsyr = models.DateField()
    mbbsmarksheet = models.FileField(upload_to='uploads/',null=True, default=None, blank=True)
    mbbsdegree = models.FileField(upload_to='uploads/')
    mdinstitution = models.CharField(max_length=25)
    mdgrade = models.CharField(max_length=10)
    mdpsyr = models.DateField()
    mdmarksheet = models.FileField(upload_to='uploads/',null=True, default=None, blank=True)
    mddegree = models.FileField(upload_to='uploads/')
    regno = models.CharField(max_length=30, null=True, default=None, blank=True)
    regfile = models.FileField(upload_to='uploads/', null=True)
    videofile = models.FileField(upload_to='uploads/')
    personal_information = models.ForeignKey(
        PersonalInformation,
        on_delete=models.CASCADE,
        default=None
    )

    def __str__(self):
        return f'{self.personal_information.first_name} {self.personal_information.last_name}'
