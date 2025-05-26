from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CampaignForm
from .models import Campaign
import logging

logger = logging.getLogger(__name__)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Campaign
from .serializers import CampaignSerializer, CampaignListSerializer

from .models import Campaign
from .serializers import CampaignSerializer, CampaignListSerializer
from system_validator.utils import validate_pdf
import logging

logger = logging.getLogger(__name__)

class CampaignCreateAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CampaignSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        category = serializer.validated_data.get('category', '').upper()
        pdf_file = request.FILES.get('document')
        
        if category == 'MEDICAL':
            if not pdf_file:
                logger.warning("Medical campaign submitted without PDF")
                return Response({'error': 'PDF document required for Medical campaigns'}, status=status.HTTP_400_BAD_REQUEST)
            
            logger.debug(f"Validating PDF: {pdf_file.name}")
            validation_result = validate_pdf(pdf_file)
            
            if validation_result['result'] == 'ACCEPTED':
                logger.info("Medical campaign approved")
                serializer.save(created_by=request.user, status='APPROVED')
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.warning(f"Medical campaign rejected: {validation_result['reason']}")
                serializer.save(created_by=request.user, status='REJECTED')
                response_data = serializer.data
                response_data['validation_reason'] = validation_result['reason']
                return Response(response_data, status=status.HTTP_201_CREATED)
        
        logger.debug("Saving non-Medical campaign")
        serializer.save(created_by=request.user, status='PENDING')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class CampaignListAPI(APIView):
    permission_classes = []
    
    def get(self, request):
        campaigns = Campaign.objects.filter(status='APPROVED')
        serializer = CampaignListSerializer(campaigns, many=True)
        return Response(serializer.data)

class AdminCampaignReviewAPI(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        campaigns = Campaign.objects.filter(status='PENDING')
        serializer = CampaignListSerializer(campaigns, many=True)
        return Response(serializer.data)
    
    def patch(self, request, campaign_id):
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            new_status = request.data.get('status')
            if new_status in ['APPROVED', 'REJECTED']:
                campaign.status = new_status
                campaign.save()
                return Response({'message': f'Campaign {new_status.lower()} successfully'})
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        except Campaign.DoesNotExist:
            return Response({'error': 'Campaign not found'}, status=status.HTTP_404_NOT_FOUND)
        



