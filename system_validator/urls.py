from .views import PDFValidationView
from django.urls import path

urlpatterns = [
    path('system_validator/', PDFValidationView.as_view(), name='validate_pdf'),
]
