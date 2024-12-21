from django.core.mail import send_mail
from django.template.loader import render_to_string
from celery import shared_task

from accounts.models import Account


@shared_task
def send_otp_email_celery(email, headline, subject, otp_code):
        
        user = Account.objects.get(email=email)
        
        # Render the email template
        context = {
            'otp': otp_code,
            'user': user,
            'headline' : headline,
        }
        message = render_to_string('emails/otp.html', context)

        # Send the email
        from_email = 'Basuri Automotive <info@basuriautomotive.com>'
        send_mail(
            subject=subject,
            message='',  # Empty plain text body
            html_message=message,  # HTML content
            from_email=from_email,
            recipient_list=[user.email]
        )