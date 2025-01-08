from django.shortcuts import get_object_or_404, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.template.loader import get_template
from xhtml2pdf import pisa



from product.models import ProductGallery
from address.models import Address
from order.models import Order, OrderItem, Shipment
from accounts.permissions import IsStaff


class OrderListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, request):
        orders = Order.objects.get_reverse_orders()
        order_list = []

        
        for order in orders:
            
            customer = order.user
            total_orders = Order.objects.filter(user=customer).count()
            items = OrderItem.objects.filter(order=order)
            item_list = []
            
            for item in items:
                product = item.product
                
                
                # site_url = request.build_absolute_uri(product.image.url)
                first_image = ProductGallery.objects.filter(product=product, type="image").order_by('position').values_list('file', flat=True).first()
                item_data = {
                    "id": item.id,
                    "product": {
                        "name": product.name,
                        "sku": product.sku,
                        "description": product.description,
                        "image": first_image
                    },
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "subtotal": str(item.subtotal)
                }
                item_list.append(item_data)
            

            # Get status history ordered by position
            stepper_data = [
                {
                    "label": history.status.name,
                    "desc": history.status.description,
                    # "icon": history.status.icon,
                    # "position": history.position,
                }
                for history in order.status_history.all()
            ]
            
            billing_address = get_object_or_404(Address, id=order.billing_address)
            shipping_address = get_object_or_404(Address, id=order.shipping_address)

            if order.so_number:
                so_number  = "true"
            else:
                so_number = "false"
            
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
                "customer_profile": {
                
                    "id": customer.id,
                    "full_name": customer.profile.first_name + ' ' + customer.profile.last_name,
                    "image" : customer.profile.image,
                    "email": customer.email,
                    "phone": customer.phone_number,
                    "total_orders": total_orders,
                },
                "billing_country": billing_address.country.name if billing_address.country else None,
                "billing_state": billing_address.state.name if billing_address.state else None,
                "shipping_country": shipping_address.country.name if shipping_address.country else None,
                "shipping_state": shipping_address.state.name if shipping_address.state else None,
                "customer_name": order.user.profile.first_name +" " + order.user.profile.last_name ,
                "created_at": order.created_at,
                "updated_at": order.updated_at,
                "sub_total": str(order.total_amount),
                "tax": str(order.tax),
                "discount": "0.00",
                "total_amount": str(order.total_amount),
                "is_paid": order.is_paid,
                "payment_date": order.payment_date,
                "payment_method": "Paypal",
                "order_date": order.order_date,
                "order_number": order.order_number,
                "order_status": stepper_data[-1]["label"] if stepper_data else "No Status",
                "stepper_data": stepper_data,
                "order_note": order.order_note,
                "provider_order_id": order.provider_order_id,
                "payment_id": order.payment_id,
                "signature_id": order.signature_id,
                "user": order.user.id,
                "currency": {
                    "id": order.currency.id,
                    "code": order.currency.code,
                    "symbol": order.currency.symbol,
                    
                } if order.currency else None,
                "shipping_charge": "0.00",
                "discount_coupon": None, 
                "erp" : bool(so_number)
            }
            # Add logistics data if shipments exist
            if order.shipments.exists():
                shipment = order.shipments.first()  # Assuming you only want the first shipment
                order_data["logistic"] = {
                    "logistic_name": shipment.logistic_name,
                    "tracking_number": shipment.tracking_number,
                    "notes": shipment.notes,
                }
            else:
                order_data["logistic"] = None  # Or omit the logistic key if not applicable
            order_list.append(order_data)

        return Response(order_list)
    
class DownloadInvoicePDFView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, request, order_id):

        single_order = get_object_or_404(Order, id=order_id)
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
    

class CreateShipmentAPIView(APIView):

    permission_classes = [IsAuthenticated, IsStaff]
    
    def post(self, request, *args, **kwargs):
        try:
            # Parse JSON data from the request body
            import json
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['order_number', 'logistic_name', 'tracking_number']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response(
                    {"error": f"Missing fields: {', '.join(missing_fields)}"},
                    status=400
                )
            
            # Validate the order
            try:
                order = Order.objects.get(order_number=data['order_number'])
            except ObjectDoesNotExist:
                return Response({"error": "Order not found."}, status=404)
            
            # Validate tracking_number uniqueness
            if Shipment.objects.filter(tracking_number=data['tracking_number']).exists():
                return Response({"error": "Tracking number already exists."}, status=400)
            
            # Create the shipment
            shipment = Shipment.objects.create(
                order=order,
                logistic_name=data['logistic_name'],
                tracking_number=data['tracking_number'],
                notes=data.get('notes', '')  # Notes are optional
            )
            
            # Return the response
            return Response({
                "order_number": shipment.order.order_number,
                "logistic_name": shipment.logistic_name,
                "tracking_number": shipment.tracking_number,
                "notes": shipment.notes
            }, status=201)
        
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format."}, status=400)
        
class UpdateShipmentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def put(self, request, *args, **kwargs):
        """
        Handle shipment updates by order number.
        """
        try:
            import json
            data = json.loads(request.body)

            # Validate required fields
            required_fields = ['order_number']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return Response(
                    {"error": f"Missing fields: {', '.join(missing_fields)}"},
                    status=400
                )

            # Find the order using the order_number
            try:
                order = Order.objects.get(order_number=data['order_number'])
            except ObjectDoesNotExist:
                return Response({"error": "Order not found."}, status=404)

            # Find the shipment associated with the order
            try:
                shipment = Shipment.objects.get(order=order)
            except Shipment.DoesNotExist:
                return Response({"error": "Shipment not found for this order."}, status=404)

            # Update fields, including the tracking number
            shipment.logistic_name = data.get('logistic_name', shipment.logistic_name)
            shipment.tracking_number = data.get('tracking_number', shipment.tracking_number)
            shipment.notes = data.get('notes', shipment.notes)

            # Check if tracking number is being updated and ensure it's unique
            new_tracking_number = data.get('tracking_number')

            if new_tracking_number and new_tracking_number != shipment.tracking_number:
                # Only check for tracking number uniqueness across all shipments except the current one
                if Shipment.objects.filter(tracking_number=new_tracking_number).exclude(id=shipment.id).exists():
                    return Response({"error": "Tracking number already exists."}, status=400)
    
            shipment.save()

            return Response({
                "order_number": shipment.order.order_number,
                "logistic_name": shipment.logistic_name,
                "tracking_number": shipment.tracking_number,
                "notes": shipment.notes
            }, status=200)

        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format."}, status=400)