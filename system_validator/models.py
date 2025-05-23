# These define the data structure for hospitals, disease types, and doctor stamps.
from django.db import models

class Hospital(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class DiseaseType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class DoctorStamp(models.Model):
    image = models.ImageField(upload_to='stamps/')

    def __str__(self):
        return f"Stamp {self.id}"
