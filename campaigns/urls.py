from django.urls import path
from . import views
from .views import CampaignCreateAPI, CampaignListAPI, AdminCampaignReviewAPI

urlpatterns = [
    path('api/campaigns/create/', CampaignCreateAPI.as_view(), name='api_campaign_create'),
    path('api/campaigns/', CampaignListAPI.as_view(), name='api_campaigns'),
    path('api/admin/review/', AdminCampaignReviewAPI.as_view(), name='api_admin_review_list'),
    path('api/admin/review/<int:campaign_id>/', AdminCampaignReviewAPI.as_view(), name='api_admin_review'),

]
