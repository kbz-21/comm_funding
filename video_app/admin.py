from django.contrib import admin
from .models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at', 'video_file')
    list_filter = ('uploaded_at',)
    search_fields = ('title',)
    ordering = ('-uploaded_at',)
    readonly_fields = ('uploaded_at',)

    def get_readonly_fields(self, request, obj=None):
        # Ensure uploaded_at is always read-only
        return self.readonly_fields

# Register your models here.
