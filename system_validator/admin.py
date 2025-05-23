from django.contrib import admin
from .models import Hospital, DiseaseType, DoctorStamp

admin.site.register(Hospital)
admin.site.register(DiseaseType)
admin.site.register(DoctorStamp)
