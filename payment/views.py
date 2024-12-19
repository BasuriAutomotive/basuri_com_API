from django.shortcuts import get_object_or_404, redirect
from paypalrestsdk import Payment
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decouple import config

from cart.models import Cart, CartItem
from order.models import Order, OrderStatus, OrderStatusHistory
from address.models import Address
from order.tasks import send_email_celery, create_erp_order_celery
# from base.tasks import send_email_celery
# from whatsapp_api.views import send_wp_message
# from order.tasks import create_erp_order_celery, send_alert_celery


current_url = settings.CURRENT_URL

def create_paypal_payment(request, order_number):
    # Order details
    
    order = Order.objects.get(order_number=order_number)
    # Create PayPal payment
    payment = Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": request.build_absolute_uri(reverse('paypal-execute')),
            "cancel_url": request.build_absolute_uri(reverse('paypal-cancel')) + f"?order_id={order.id}"
        },
        "transactions": [{
            "amount": {
                "total": str(order.total_amount),
                "currency": order.currency.code
            },
            "description": "Order payment"
        }]
    })
    if payment.create():
        # Save payment_id to the order
        order.payment_id = payment.id
        order.save()
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = link.href
                return approval_url
    else:
        return Response({"error": payment.error}, status=status.HTTP_400_BAD_REQUEST)
        
class ExecutePayPalPaymentAPIView(APIView):
    def get(self, request):
        payment_id = request.query_params.get('paymentId')
        payer_id = request.query_params.get('PayerID')

        order = get_object_or_404(Order, payment_id=payment_id)

        payment = Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            # Payment executed successfully
            # Redirect to your React app's success path with payment_id as a query parameter
            
            success_url = current_url + f"order/order-complete?id={order.id}"

            # remove cart item
            try:
                if order.checkout_type == 'cart':
                    CartItem.objects.filter(user=order.user).delete()
            except:
                pass
            
            return redirect(success_url)
        else:
            # Handle payment execution failure
            failure_url = current_url + f"order/payment-fail?id={order.id}"
            return redirect(failure_url)

class CancelPayPalPaymentAPIView(APIView):
    def get(self, request):
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response({"error": "Order id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Optionally update the order status to "cancelled" if necessary
        # Order.objects.filter(order_number=order_number).update(is_paid=False, status='cancelled')
        
        # Redirect to your React route for payment cancellation
        failure_url = current_url + f"order/payment-fail?id={order_id}"
        return redirect(failure_url)

class FinalizeOrderAfterPaymentAPIView(APIView):
    def post(self, request):
        order_id = request.data.get('order_id')
        cart_id = request.data.get('cart_id', None)
        # Find the payment and the associated order
        print("step-1")
        try:
            order = get_object_or_404(Order, id=order_id)
            payment = Payment.find(order.payment_id)

            if payment.state == "approved":
                # Payment was successful
                order.is_paid = True
                order.save()

                try:
                    if order.checkout_type == 'cart':
                        # Clear the user's cart
                        print("step-2")
                        if cart_id :
                            print("step-3")
                            cart = Cart.objects.get(cart_id=cart_id)
                            CartItem.objects.filter(cart=cart).delete()
                            a = CartItem.objects.filter(cart=cart)
                            print(a)
                except:
                    pass

                # Prepare success response
                response_data = {
                    "order_date": order.order_date,
                    "order_number": order.order_number,
                    "payment_method": "Paypal",
                    "tax": str(order.tax),
                    "sub_total": order.total_amount,
                    "total_amount": str(order.total_amount),
                    "discount_amount": order.discount_amount ,
                    "currency": order.currency.code,
                    "order_items": [
                        {
                            "product_id": item.product.id,
                            "product_name": item.product.name,
                            "quantity": item.quantity,
                            "unit_price": str(item.unit_price),
                            "subtotal": str(item.subtotal),
                        }
                        for item in order.items.all()
                    ]
                }


               
                
                # try:
                #     template_id = 'basuriautomotive_com_order_confirmation_v1'
                #     name = order.user.profile.first_name + ' ' + order.user.profile.last_name
                #     order_number_wp = "#" + order.order_number
                #     date = "Nov 20, 2024"
                #     print(template_id, order.user.phone_number, date, name, order_number_wp)
                #     billing  = Address.objects.get(id=order.billing_address)
                #     if no_production == False:
                #         tracking = True
                #         # send_wp_message(name, order_number_wp, date, template_id, billing.contact_phone)
                # except :
                #     pass

                order_items = []
                
                for item in order.items.all():
                    first_image = (
                        item.product.product_gallery.filter(type="image").order_by("position").first()
                    )
                    order_items.append({
                        "product": item.product,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "first_image": first_image,  # Add the first image
                    })


                # SEND CONFIRMATION EMAIL TO CUSTOMER
                try:
                    message = {
                    'single_order' : order,
                    'order_items' : order_items,
                    }
                    message = render_to_string("emails/orders/confirmation.html", message)
                    subject= "Order Confirmation"
                    email = order.user.email
                    send_email_celery.delay(message, subject, email)
                except:
                    pass


                # CREATE ORDER ON ERP
                try:
                    # no_production =  config('DEBUG', default=False, cast=bool)
                    erp_connection =  config('ERP_CONNECTION', default=False, cast=bool)
                    if erp_connection == True:
                        create_erp_order_celery.delay(order.order_number)
                except :
                    pass

                try:
                    # Fetch the "Payment Confirmed" status
                    payment_confirmed_status = OrderStatus.objects.get(name="Payment Confirmed")
                    
                    # Create the history entry
                    OrderStatusHistory.objects.create(
                        order=order,
                        status=payment_confirmed_status,
                    )
                except OrderStatus.DoesNotExist:
                    # Log or handle the error if "Payment Confirmed" status is missing
                    print("OrderStatus 'Payment Confirmed' does not exist.")

                return Response(response_data, status=status.HTTP_200_OK)
            

            else:
                # Handle payment not approved
                response_data = {
                    "detail": "Payment not approved",
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "error": "Payment was not approved."
                }
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        



class RetryExistingPayPalPaymentAPIView(APIView):
    
    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        payment_id = order.payment_id
        # Validate that the payment ID is provided
        if not payment_id:
            return Response({"error": "Payment ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Fetch the existing PayPal payment
            payment = Payment.find(payment_id)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Redirect the user to the approval URL to complete the payment
        for link in payment.links:
            if link.rel == "approval_url":
                approval_url = link.href
                return Response({"approval_url": approval_url}, status=status.HTTP_200_OK)
        
        return Response({"error": "Approval URL not found in the payment object."}, status=status.HTTP_400_BAD_REQUEST)