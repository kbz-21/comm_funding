from django import forms
from .models import Campaign

class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = [
            'title', 
            'category',
            'description', 
            'starting_date', 
            'ending_date', 
            'goal_amount', 
            'location',
            'image',
            'document'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'starting_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ending_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'goal_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
