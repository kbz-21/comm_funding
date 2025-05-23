from django.contrib import admin
from .models import Campaign

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'goal_amount', 'starting_date', 'ending_date', 'created_by', 'created_at')
    list_filter = ('category', 'status', 'starting_date', 'ending_date')
    search_fields = ('title', 'description', 'location', 'created_by__email')
    ordering = ('-created_at',)

# Register your models here.
