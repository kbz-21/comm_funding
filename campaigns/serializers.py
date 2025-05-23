from rest_framework import serializers
from .models import Campaign

class CampaignSerializer(serializers.ModelSerializer):
    document = serializers.FileField(required=True)
    image = serializers.ImageField(required=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'title', 'category', 'description', 'goal_amount',
            'starting_date', 'ending_date', 'location', 'image',
            'document', 'status', 'created_by', 'created_at'
        ]
        read_only_fields = ['status', 'created_by', 'created_at']

    def validate_document(self, value):
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Document must be a PDF file.")
        return value

class CampaignListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            'id', 'title', 'category', 'description', 'goal_amount',
            'starting_date', 'ending_date', 'location', 'image',
            'document', 'status', 'created_at'
        ]