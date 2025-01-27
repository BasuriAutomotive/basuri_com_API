from decimal import Decimal
from django.shortcuts import get_object_or_404, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.template.loader import get_template
from xhtml2pdf import pisa


from address.models import Address
from product.models import ProductGallery
from .models import Order, OrderItem, OrderStatus, OrderStatusHistory


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user, is_paid=True)
        order_list = []

        for order in orders:
            items = OrderItem.objects.filter(order=order)
            item_list = []

            for item in items:
                product = item.product
                
                
                # site_url = request.build_absolute_uri(product.image.url)

                # Fetch the first image for the product
                first_image = ProductGallery.objects.filter(product=product, type="image").order_by('position').values_list('file', flat=True).first()

                item_data = {
                    "product": {
                        "name": product.name,
                        "description": product.description,
                        "image": first_image
                    },
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "subtotal": str(item.subtotal)
                }
                item_list.append(item_data)

            
            billing_address = get_object_or_404(Address, id=order.billing_address)
            shipping_address = get_object_or_404(Address, id=order.shipping_address)

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

            # Fetch the first image for the product
            first_image = ProductGallery.objects.filter(product=product, type="image").order_by('position').values_list('file', flat=True).first()

            item_data = {
                "product": {
                    "name": product.name,
                    "description": product.description,
                    "image": first_image
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
        email = email.lower()

        if not order_number or not email:
            return Response({"detail": "Order number and email are required."}, status=400)

        try:
            order = Order.objects.get(order_number=order_number, user__email=email)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found or email does not match."}, status=404)

        # Fetch the status history for the order
        status_history = OrderStatusHistory.objects.filter(order=order).order_by('position')
        
        # Construct stepper_data from status history
        stepper_data = []
        for status_entry in status_history:
            stepper_data.append({
                "label": status_entry.status.name,
                "desc": status_entry.status.description or "",
                "status": True  # Since it's in history, the status is achieved
            })
        
        # Ensure any remaining statuses are marked as pending
        all_statuses = OrderStatus.objects.all()
        completed_status_ids = status_history.values_list('status_id', flat=True)
        for status in all_statuses:
            if status.id not in completed_status_ids:
                stepper_data.append({
                    "label": status.name,
                    "desc": status.description or "",
                    "status": False  # Status not yet achieved
                })

        # Fetch order items
        items = []
        sub_total = Decimal("0.00")
        order_items = order.items.all()  # Assuming related_name="order_items" in OrderItem model
        for item in order_items:
            product = item.product
            item_subtotal = Decimal(item.quantity) * item.unit_price
            # Fetch the first image for the product
            first_image = ProductGallery.objects.filter(product=product, type="image").order_by('position').values_list('file', flat=True).first()
            items.append({
                "product": {
                    "image": first_image,
                    "name": product.name,
                },
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "subtotal": f"{item_subtotal:.2f}",
            })
            sub_total += item_subtotal  # Add subtotal to the main sub_total

        # Construct response data
        response_data = {
            "order_id": order.id,
            "stepper_data": stepper_data,
            "items": items,
            "sub_total": f"{sub_total:.2f}",  # Assuming `sub_total` field exists
            "discount": str(order.discount) if hasattr(order, 'discount') else "0.00",
            "total_amount": str(order.total_amount),
        }

        return Response(response_data, status=200)

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