from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Coupon

class ApplyCouponAPIView(APIView):

    def post(self, request):
        code = request.data.get('code')
        order_total = request.data.get('order_total')

        if not code or not order_total:
            return Response({"detail": "Coupon code and order total are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            coupon = Coupon.objects.get(code=code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
        except Coupon.DoesNotExist:
            return Response({"detail": "Invalid or expired coupon code."}, status=status.HTTP_400_BAD_REQUEST)

        # For authenticated users
        user = request.user if request.user.is_authenticated else None

        if user and coupon.used_by.filter(id=user.id).exists():
            return Response({"detail": "Coupon code has already been used by this user."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate discount amount
        discount_amount = coupon.calculate_discount_amount(order_total)
        updated_order_total = float(order_total) - discount_amount

        return Response({
            "code": coupon.code,
            "discount_percentage": coupon.discount_percentage,
            "discount_amount": discount_amount,
            "order_total": updated_order_total
        }, status=status.HTTP_200_OK)

