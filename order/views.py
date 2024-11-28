from django.shortcuts import get_object_or_404, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.template.loader import get_template
from xhtml2pdf import pisa

from product.models import ProductGallery
from accounts.models import Account
from address.models import Address
from .models import Order, OrderItem


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user, is_paid=True)
        order_list = []

        print("1")
        for order in orders:
            items = OrderItem.objects.filter(order=order)
            item_list = []
            print("2")
            for item in items:
                product = item.product
                
                
                # site_url = request.build_absolute_uri(product.image.url)

                item_data = {
                    "product": {
                        "name": product.name,
                        "description": product.description,
                        "image": ""
                    },
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "subtotal": str(item.subtotal)
                }
                item_list.append(item_data)
            print("3")
            print(order.billing_address)
            print(order.shipping_address)

            
            billing_address = get_object_or_404(Address, id=order.billing_address)
            shipping_address = get_object_or_404(Address, id=order.shipping_address)

            print("4")
            order_data = {
                "id": order.id,
                "items": item_list,
                "billing_address": {
                    "id": billing_address.id,
                    "country": {"name": billing_address.country.name if billing_address.country else None},
                    "state": {"name": billing_address.state.name if billing_address.state else None},
                    "street": billing_address.address_line_1,
                    "street2": billing_address.address_line_2,
                    "city": billing_address.city if billing_address.city else None,
                    "zip": billing_address.zip_code,
                    "contact_person": billing_address.contact_person,
                    "contact_phone": billing_address.contact_phone,
                },
                "shipping_address": {
                    "id": shipping_address.id,
                    "country": {"name": shipping_address.country.name if shipping_address.country else None},
                    "state": {"name": shipping_address.state.name if shipping_address.state else None},
                    "street": shipping_address.address_line_1,
                    "street2": shipping_address.address_line_2,
                    "city": shipping_address.city if shipping_address.city else None,
                    "zip": shipping_address.zip_code,
                    "contact_person": shipping_address.contact_person,
                    "contact_phone": shipping_address.contact_phone,
                },
                "billing_country": billing_address.country.name if billing_address.country else None,
                "billing_state": billing_address.state.name if billing_address.state else None,
                "shipping_country": shipping_address.country.name if shipping_address.country else None,
                "shipping_state": shipping_address.state.name if shipping_address.state else None,
                "created_at": order.created_at,
                "updated_at": order.updated_at,
                "sub_total": str(order.total_amount),
                "tax": str(order.tax),
                "discount": "0.00",  # Assuming there's no discount field in the model
                "total_amount": str(order.total_amount),
                "is_paid": order.is_paid,
                "payment_date": order.payment_date,
                "payment_method": "Paypal",  # Assuming the payment method is Paypal
                "order_date": order.order_date,
                "order_number": order.order_number,
                "order_status": "status",
                "order_note": order.order_note,
                "provider_order_id": order.provider_order_id,
                "payment_id": order.payment_id,
                "signature_id": order.signature_id,
                "user": order.user.id,
                "currency": order.currency.id if order.currency else None,
                "shipping_charge": "0.00",  # Assuming there's no shipping charge field in the model
                "discount_coupon": None  # Assuming there's no discount coupon field in the model
            }
            order_list.append(order_data)

        return Response(order_list)

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user = request.user
        order = get_object_or_404(Order, id=order_id, user=user)
        
        items = OrderItem.objects.filter(order=order)
        item_list = []

        for item in items:
            product = item.product
            # galleries = ProductGallery.objects.filter(product=product)
            # gallery_list = [{"image": gallery.image.url, "alt": product.name} for gallery in galleries]

            item_data = {
                "product": {
                    "name": product.name,
                    "description": product.description,
                    "image": ""
                },
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal)
            }
            item_list.append(item_data)

        billing_address = get_object_or_404(Address, id=order.billing_address)
        shipping_address = get_object_or_404(Address, id=order.shipping_address)

        
       
        order_status = "Delivered"



        order_data = {
            "id": order.id,
            "items": item_list,
            "billing_address": {
                "id": billing_address.id,
                "country": {"name": billing_address.country.name if billing_address.country else None},
                "state": {"name": billing_address.state.name if billing_address.state else None},
                "street": billing_address.address_line_1,
                "street2": billing_address.address_line_2,
                "city": billing_address.city if billing_address.city else None,
                "zip": billing_address.zip_code,
                "contact_person": billing_address.contact_person,
                "contact_phone": billing_address.contact_phone,
            },
            "shipping_address": {
                "id": shipping_address.id,
                "country": {"name": shipping_address.country.name if shipping_address.country else None},
                "state": {"name": shipping_address.state.name if shipping_address.state else None},
                "street": shipping_address.address_line_1,
                "street2": shipping_address.address_line_2,
                "city": shipping_address.city if shipping_address.city else None,
                "zip": shipping_address.zip_code,
                "contact_person": shipping_address.contact_person,
                "contact_phone": shipping_address.contact_phone,
            },
            "billing_country": billing_address.country.name if billing_address.country else None,
            "billing_state": billing_address.state.name if billing_address.state else None,
            "shipping_country": shipping_address.country.name if shipping_address.country else None,
            "shipping_state": shipping_address.state.name if shipping_address.state else None,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "sub_total": str(order.total_amount),
            "tax": str(order.tax),
            "discount": order.discount_amount,  # Assuming there's no discount field in the model
            "total_amount": str(order.total_amount),
            "is_paid": order.is_paid,
            "payment_date": order.payment_date,
            "payment_method": "Paypal",  # Assuming the payment method is Paypal
            "order_date": order.order_date,
            "order_number": order.order_number,
            "order_status": order_status,
            "order_note": order.order_note,
            "provider_order_id": order.provider_order_id,
            "payment_id": order.payment_id,
            "signature_id": order.signature_id,
            "user": order.user.id,
            "currency": order.currency.id if order.currency else None,
            "shipping_charge": "0.00",  # Assuming there's no shipping charge field in the model
            "discount_coupon": None  # Assuming there's no discount coupon field in the model
        }

        return Response(order_data)
    
class OrderTrackingAPIView(APIView):

    def post(self, request):
        order_number = request.data.get('order_number')
        email = request.data.get('email')

        if not order_number or not email:
            return Response({"detail": "Order number and email are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(order_number=order_number, user__email=email)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found or email does not match."}, status=status.HTTP_404_NOT_FOUND)

        stepper_data = [
            {
                "label": "Order Placed",
                "desc": "Your order has been placed successfully.",
                "status": order.order_status in ['Pending', 'Accepted', 'Dispatch', 'Deliverd'],
            },
            {
                "label": "Dispatch",
                "desc": "Your order has been dispatched.",
                "status": order.order_status in ['Dispatch', 'Deliverd'],
            },
            {
                "label": "Delivered",
                "desc": "Your order has been delivered.",
                "status": order.order_status == 'Deliverd',
            },
        ]

        # Get order items
        items = []
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            product = item.product
            product_data = {
                "product": {
                    "image": "https://basuriautomotive.com" + product.image.url if product.image else None,
                    "name": product.name,
                },
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": str(item.subtotal),
            }
            items.append(product_data)

        response_data = {
            "order_id": order.id,
            "stepper_data": stepper_data,
            "items": items,
            "sub_total": str(order.total_amount),
            "discount": "0.00",
            "total_amount": str(order.total_amount),
        }

        return Response(response_data)

class DownloadInvoicePDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user = request.user
        single_order = get_object_or_404(Order, id=order_id, user=user)
        shipping_address = get_object_or_404(Address, id=int(single_order.shipping_address))
        order_items = OrderItem.objects.filter(order=single_order)
        
        template = get_template('invoice.html')
        context = {
            'single_order': single_order,
            'shipping_address': shipping_address,
            'order_items': order_items,
        }
        html = template.render(context)
        
        
        # GENERATE PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
        
        pdf = pisa.CreatePDF(html, dest=response)
        if pdf.err:
            return HttpResponse('Error generating PDF file')
        
        return response
    

