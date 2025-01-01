import uuid
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework import status
from django.utils.timezone import now
from datetime import datetime, timedelta, date
from requests import Response
from rest_framework.response import Response as response

from accounts.models import Account
from discount.models import Coupon
from utils.models import OTP
from .models import MenuItem, Newsletter
from .tasks import send_otp_email_task


def build_menu_tree(menu_items):
    menu_dict = {}
    for item in menu_items:
        item['url'] = item['url'].replace('https://basuriautomotive.com', '')
        item['children'] = []
        menu_dict[item['id']] = item
    root_items = []
    for item in menu_items:
        if item['parent_id']:
            parent = menu_dict[item['parent_id']]
            parent['children'].append(item)
        else:
            root_items.append(item)
    return root_items


@method_decorator(csrf_exempt, name='dispatch')
class MenuItemListCreateView(View):
    def get(self, request):
        menu_items = MenuItem.objects.all().values().order_by('position')
        menu_tree = build_menu_tree(menu_items)
        return JsonResponse(menu_tree, safe=False)


def send_otp(email, headline, subject):
    try : 
        user = Account.objects.get(email=email)
    except:
        return Response({"detail": "User does not exist!"}, status=status.HTTP_400_BAD_REQUEST)
    otp = OTP.generate_otp(user)
    send_otp_email_task.delay(user.email, headline, subject, otp.otp_code)
    valid_till = datetime.now() + timedelta(minutes=3)
    return valid_till


def validate_otp(user, otp_code):
    try:
        otp = OTP.objects.get(user=user, otp_code=otp_code, is_used=False)
        if otp.is_expired():
            return False, "OTP has expired."
        otp.is_used = True
        otp.save()
        return True, "Success! The OTP you entered is valid."
    except OTP.DoesNotExist:
        return False, "The OTP you entered is incorrect. Check and re-enter."
    

def resend_otp(email, headline, subject, validity_period=15):
    try : 
        user = Account.objects.get(email=email)
    except:
        return Response({"detail": "User does not exist!"}, status=status.HTTP_400_BAD_REQUEST)
    existing_otp = OTP.objects.filter(user=user, is_used=False, expires_at__gt=now()).first()
    if existing_otp:
        existing_otp.expires_at = now() + timedelta(minutes=validity_period)
        existing_otp.save()
        otp_to_send = existing_otp.otp_code
    else:
        OTP.objects.filter(user=user, is_used=False, expires_at__gt=now()).update(is_used=True)
        new_otp = OTP.generate_otp(user)
        otp_to_send = new_otp.otp_code
    send_otp_email_task.delay(user.email, headline, subject, otp_to_send)
    return existing_otp if existing_otp else new_otp



class NewsletterView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return response({"error": "Email is required"}, status=400)

        try:
            # Check if already subscribed
            subscriber, created = Newsletter.objects.get_or_create(email=email)
            if not created:
                return response({"message": "You are already subscribed!"}, status=200)

            # Generate a coupon for the subscriber
            coupon = create_newsletter_coupon(email)

            # Send response with the coupon code
            return response({"message": "Subscription successful! Check email for discount code"}, status=200)
        except Exception as e:
            return response({"error": str(e)}, status=500)
        

def create_newsletter_coupon(email):
    # Generate a unique coupon code
    coupon_code = f"B10{uuid.uuid4().hex[:6].upper()}"

    # Set coupon details
    discount_percentage = 10  # First-time discount
    valid_from = date.today()
    valid_to = valid_from + timedelta(days=30)  # Valid for 30 days

    # Create the coupon
    coupon = Coupon.objects.create(
        code=coupon_code,
        discount_percentage=discount_percentage,
        valid_from=valid_from,
        valid_to=valid_to
    )
    return coupon