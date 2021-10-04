# celery -A <project> worker --loglevel=INFO --without-gossip --without-mingle --without-heartbeat -Ofair --pool=solo
# Celery beat somehow only works when I run the celery service with the options above.

from celery import shared_task
from .models import *
from django.core.mail import send_mail
from datetime import datetime, timedelta

@shared_task
def add(x, y):
    return x + y

@shared_task
def test_email(message:str="", html_message:str="") -> None:
    send_mail(
        'Bitesize Notification', 
        message, 
        'bitesize@elvnosix.com', 
        ['manjaka.andriamasinoro@gmail.com'], 
        fail_silently=False,
        html_message=html_message,
    )

# sends a weekly email to all subscribed users with all steps due for the week
@shared_task
def send_weekly_email() -> None:
    users = User.objects.filter(subscribed=True)
    for user in users:
        # Get all the user steps due this week
        steps = Step.objects.filter(user_id=user, complete=False, deadline__range=[datetime.now().date(), datetime.now().date() + timedelta(days=7)])
        if steps:
            html_steps = ""
            for step in steps:
                html_steps += f"<li>{step.name}</li>"
            html_message = f"<h3> Hi {user.firstname or user.username},</h3> <p>Here are the steps waiting for you this week:</p> <ul>{html_steps}</ul> <h5>{user.encouragement}</h5><p>You can opt out of email notifications by logging into Bitesize, clicking on Profile and unchecking 'Subscribed to email notifications'</p>"
            send_mail(
                subject='Your Bitesize steps this week',
                message="",
                html_message=html_message,
                from_email='Bitesize@elvnosix.com',
                recipient_list=[user.email],
                fail_silently=False)