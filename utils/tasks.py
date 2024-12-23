from django.core.mail import send_mail
from django.template.loader import render_to_string
from celery import shared_task

from accounts.models import Account

@shared_task(name='email_notification')
def send_email_task(message, subject, email):
    from_email = 'Basuri Automotive <info@basuriautomotive.com>' # SYSTEM SENDER EMAIL
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list, html_message=message)
    return email


@shared_task(name='otp_email')
def send_otp_email_task(email, headline, subject, otp_code):     
    try:
        user = Account.objects.get(email=email)
    except:
        pass
    
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
    return user.email