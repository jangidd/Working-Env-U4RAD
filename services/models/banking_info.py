from django.db import models
from .personal_info import PersonalInformation

class BankingDetails(models.Model):
    accholdername = models.CharField(max_length=25)
    bankname = models.CharField(max_length=25)
    branchname = models.CharField(max_length=25)
    acnumber = models.CharField(max_length=15)
    ifsc = models.CharField(max_length=15)
    pancardno = models.CharField(max_length=10)
    aadharcardno = models.CharField(max_length=12)
    pancard = models.FileField(upload_to='uploads/')
    aadharcard = models.FileField(upload_to='uploads/')
    cheque = models.FileField(upload_to='uploads/')
    personal_information = models.ForeignKey(
        PersonalInformation,
        on_delete=models.CASCADE,
        default=None  # Replace with the default value you want to use
    )

    def __str__(self):
        return self.personal_information.first_name + self.personal_information.last_name