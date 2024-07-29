from django.contrib import admin
from .models.models import Service, ServiceRate
from .models.profile import Profile, UploadFile
from .models.CartItem import Cart
from .models.CartValue import CartValue
from .models.Order import Order
from .models.OrderHistory import OrderHistory
from .models.personal_info import PersonalInformation
from .models.educational_info import EducationalDetails
from .models.workexp_info import ExperienceDetails
from .models.achievement_info import AchievementDetails
from .models.banking_info import BankingDetails
from .models.reportingarea_info import ReportingAreaDetails
from .models.timeavailability_info import AvailabilityDetails
from .models.ratelist import RateList
from .models.CallbackForm import Callback

class ServiceRateInline(admin.TabularInline):
    model = ServiceRate
    extra = 1

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'is_active', 'added_date', 'modified_date')
    inlines = [ServiceRateInline]
    readonly_fields = ('added_date', 'modified_date')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.added_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

class UploadFileInline(admin.TabularInline):
    model = UploadFile
    extra = 1

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'address', 'organization', 'get_uploads')
    inlines = [UploadFileInline]

    def get_uploads(self, obj):
        return ", ".join([f.file.url for f in obj.uploads.all()])

    get_uploads.short_description = 'Uploaded Files'

admin.site.register(Service, ServiceAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Cart)
admin.site.register(CartValue)
admin.site.register(Order)
admin.site.register(OrderHistory)
admin.site.register(PersonalInformation)
admin.site.register(EducationalDetails)
admin.site.register(ExperienceDetails)
admin.site.register(AchievementDetails)
admin.site.register(BankingDetails)
admin.site.register(ReportingAreaDetails)
admin.site.register(AvailabilityDetails)
admin.site.register(Callback)
admin.site.register(RateList)
