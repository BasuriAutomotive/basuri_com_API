import json
import stripe
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decouple import config
from paypalrestsdk import Payment

from cart.models import Cart, CartItem
from order.models import Order, OrderStatus, OrderStatusHistory
from utils.tasks import send_email_task
from order.tasks import create_erp_order_task
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
        order_id = request.data.get('order_id', None)
        cart_id = request.data.get('cart_id', None)
        payment_intent_id = request.data.get('payment_intent', None)
        print(order_id)
        if order_id == None:
            # Fetch the Payment Intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            # Retrieve the order_id from metadata
            order_id = payment_intent.metadata.get("order_id")   
            if not order_id:
                return JsonResponse({"error": "Order ID not found in metadata."}, status=404)

        order = get_object_or_404(Order, id=order_id)

        try:

            if order.payment_type == "stripe" or order.payment_type == "credit_card":
                
                if not payment_intent_id:
                    return JsonResponse({"error": "Payment Intent ID is required."}, status=400)

                try:

                    if payment_intent.status == "succeeded":
                        # Mark the order as paid in the database
                        order.payment_id = payment_intent_id
                        order.is_paid = True
                        order.save()


                        try:
                            if order.checkout_type == 'cart':
                                # Clear the user's cart
                                if cart_id :
                                    cart = Cart.objects.get(cart_id=cart_id)
                                    CartItem.objects.filter(cart=cart).delete()
                                    a = CartItem.objects.filter(cart=cart)
                        except:
                            pass

                        if order.payment_type == "credit_card":
                            order_payment_type = "Card Payment"

                        elif order.payment_type == "stripe":
                            order_payment_type = "Stripe"
                        # Prepare success response
                        response_data = {
                            "order_date": order.order_date,
                            "order_number": order.order_number,
                            "payment_method": order_payment_type,
                            "tax": str(order.tax),
                            "sub_total": order.total_amount,
                            "total_amount": str(order.total_amount),
                            "discount_amount": order.discount_amount ,
                            "currency": {
                                    "code": order.currency.code,
                                    "symbol": order.currency.symbol,
                                    "currency_type": order.currency.currency_type,
                                },
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
                            send_email_task.delay(message, subject, email)
                        except:
                            pass


                        # CREATE ORDER ON ERP
                        try:
                            # no_production =  config('DEBUG', default=False, cast=bool)
                            erp_connection =  config('ERP_CONNECTION', default=False, cast=bool)
                            if erp_connection == True:
                                create_erp_order_task.delay(order.order_number)
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
                        except:
                            pass

                        return Response(response_data, status=status.HTTP_200_OK)

                    else:
                        return JsonResponse({"status": "failed", "message": "Payment not successful."})
                except stripe.error.StripeError as e:
                    return JsonResponse({"error": str(e)}, status=400)

            elif order.payment_type == "paypal":


                payment = Payment.find(order.payment_id)

                if payment.state == "approved":
                    # Payment was successful
                    order.is_paid = True
                    order.save()

                    try:
                        if order.checkout_type == 'cart':
                            # Clear the user's cart
                            if cart_id :
                                cart = Cart.objects.get(cart_id=cart_id)
                                CartItem.objects.filter(cart=cart).delete()
                                a = CartItem.objects.filter(cart=cart)
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
                        "currency": {
                                    "code": order.currency.code,
                                    "symbol": order.currency.symbol,
                                    "currency_type": order.currency.currency_type,
                                },
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
                        send_email_task.delay(message, subject, email)
                    except:
                        pass


                    # CREATE ORDER ON ERP
                    try:
                        # no_production =  config('DEBUG', default=False, cast=bool)
                        erp_connection =  config('ERP_CONNECTION', default=False, cast=bool)
                        if erp_connection == True:
                            create_erp_order_task.delay(order.order_number)
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
                    except:
                        pass

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
    

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_payment_intent(request, amount, currency, order_id):
    
    try:
        print(amount, "sssss")
        print(currency, "sssss")
        # Create PaymentIntent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            automatic_payment_methods={"enabled": True},  # Enables card payments
            metadata={
                "order_id": order_id,  # Add your order ID here
            },
        )
        return payment_intent["client_secret"]
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)



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