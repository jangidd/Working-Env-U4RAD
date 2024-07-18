from django import forms
from .models.models import Service, ServiceRate
from .models.profile import Profile

################ multiform imports ########################
#--------------------Himanshu-----------------------------#
from .models.personal_info import PersonalInformation
from .models.educational_info import EducationalDetails
from .models.workexp_info import ExperienceDetails
from .models.achievement_info import AchievementDetails
from .models.banking_info import BankingDetails
from .models.reportingarea_info import ReportingAreaDetails
from .models.timeavailability_info import AvailabilityDetails
from .models.CallbackForm import Callback

############## End of Multiform imports ###################

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['service_name', 'is_active']

class ServiceRateForm(forms.ModelForm):
    class Meta:
        model = ServiceRate
        fields = ['service', 'min_quantity', 'max_quantity', 'rate']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['email', 'address', 'organization']          


################### Multiform classes ######################
#--------------------- Himanshu ---------------------------#
class CallbackForm(forms.ModelForm):
    class Meta:
        model = Callback
        fields = '__all__'

class PersonalInformationForm(forms.ModelForm):
    class Meta:
        model = PersonalInformation
        fields = '__all__'

class EducationalInfoForm(forms.ModelForm):
    class Meta:
        model = EducationalDetails
        fields = '__all__'

    tenthcertificate = forms.FileField(required=False)
    twelthcertificate = forms.FileField(required=False)
    mbbsmarksheet = forms.FileField(required=False)
    mbbsdegree = forms.FileField(required=False)
    mdmarksheet = forms.FileField(required=False)
    mddegree = forms.FileField(required=False)
    videofile = forms.FileField(required=False)

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = ExperienceDetails
        fields = '__all__'

class AchievementsInfoForm(forms.ModelForm):
    class Meta:
        model = AchievementDetails
        fields = '__all__'

class BankingDetailsForm(forms.ModelForm):
    class Meta:
        model = BankingDetails
        fields = '__all__'

####################### End of multiform classes #############################