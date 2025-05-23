from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    video_file = serializers.FileField()

    class Meta:
        model = Video
        fields = ['id', 'title', 'video_file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']