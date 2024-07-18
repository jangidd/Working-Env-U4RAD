from django.db import models

class PersonalInformation(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    password = models.CharField(max_length=15, null=True, default=None, blank=True)
    cnfpassword = models.CharField(max_length=15, null=True, default=None, blank=True)
    address = models.CharField(max_length=200)
    contact_no = models.CharField(max_length=15)
    resume = models.FileField(upload_to='uploads/')
    photo = models.ImageField(upload_to='uploads/')
    experience_years = models.PositiveIntegerField()
    # status = models.CharField(max_length=20, choices=[('under_progress', 'Under Progress'), ('completed', 'Completed')], default='under_progress', null=False)
    stage1status = models.CharField(max_length=23, choices=[('applied', 'Applied'), ('under_progress', 'Under Progress'), ('verified_by_coordinator', 'Verified by Coordinator'), ('verification_failed', 'Verification Failed')], default='applied')
    stage2status = models.CharField(max_length=28, choices=[('applied', 'Applied'), ('under_progress', 'Under Progress'), ('verified_by_supercoordinator', 'Verified by Supercoordinator'), ('verification_failed', 'Verification Failed')], default='applied')
    coordinator_message = models.CharField(max_length=100, null=True, default=None, blank=True)
    supercoordinator_message = models.CharField(max_length=100, null=True, default=None, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
