from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, FileExtensionValidator
from datetime import date
from django.conf import settings

class Campaign(models.Model):
    CATEGORY_CHOICES = (
        ('ACADEMIC', 'Academic'),
        ('NATURAL_DISASTER', 'Natural Disaster'),
        ('EMERGENCY', 'Emergency'),
        ('MEDICAL', 'Medical'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    title = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    starting_date = models.DateField()
    ending_date = models.DateField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='images/')
    document = models.FileField(
        upload_to='documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.starting_date < date.today():
            raise ValidationError("Starting date cannot be in the past.")
        if self.ending_date <= self.starting_date:
            raise ValidationError("Ending date must be after starting date.")

# Create your models here.
