# campaign/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from .models import Campaign

@shared_task
def send_campaign_status_email(campaign_id):
    campaign = Campaign.objects.get(id=campaign_id)
    email = campaign.created_by.email
    subject = f"Campaign {campaign.status}"
    if campaign.campaign_type != "Medical":
        if campaign.status == "Approved":
            message = f"Dear {campaign.created_by.username},\n\nYour campaign '{campaign.title}' has been approved!"
        elif campaign.status == "Rejected":
            message = f"Dear {campaign.created_by.username},\n\nYour campaign '{campaign.title}' has been rejected."
        else:
            return  # No email for other statuses
        send_mail(
            subject,
            message,
            'from@example.com',
            [email],
            fail_silently=False,
        )