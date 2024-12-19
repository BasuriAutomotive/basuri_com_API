from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from order.models import Order, OrderItem, OrderStatus, OrderStatusHistory
from payment.views import create_paypal_payment
from product.models import Currencies, Product, ProductPrice
from cart.models import Cart, CartItem
from discount.models import Coupon
from accounts.models import Account, Profile
from address.models import Address, Country, State
from django.utils import timezone
from decimal import Decimal
from django.conf import settings

current_url = settings.CURRENT_URL

class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print("working")
        data = request.data
        print(data)
        user = request.user if request.user.is_authenticated else None
        print(user)
        
        # Extracting order details
        country_code = data.get('country_code', 'US')
        page_location = data.get('page_location')
        print(page_location)
        billing_address_id = data.get('billing_address')
        print(billing_address_id)
        shipping_address_id = data.get('shipping_address')
        print(billing_address_id)
        discount_code = data.get('discount_code')
        # currency_code = data.get('currency')
        tax = data.get('tax')
        order_note = data.get('order_note')
        
        # Fetching Address instances
        billing_address = get_object_or_404(Address, id=billing_address_id)
        shipping_address = get_object_or_404(Address, id=shipping_address_id)
        print(billing_address)
        print(shipping_address)
        currency = get_object_or_404(Currencies, countries__code=country_code)

        print(page_location)
        subtotal=Decimal(0)
       
        if page_location == "cart":
            # Fetch cart items
            cart_items = CartItem.objects.filter(user=user)  # Assuming CartItem is related to the user
            print('cart')
            # Check if cart is empty
            if not cart_items.exists():
                return Response({"detail": "No items in cart to create an order."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            sku = data.get('product_sku')
            print('no cart')
            product = Product.objects.get(sku=sku)
        
        current_datetime = timezone.now()
        year = current_datetime.strftime('%Y')
        month = current_datetime.strftime('%m')
        timestamp = int(current_datetime.timestamp())
        order_number = f"BA{month}{year}{timestamp}"

        # Create order
        order = Order.objects.create(
            user=user,
            billing_address=billing_address.id,
            shipping_address=shipping_address.id,
            country=billing_address.country.name,  # Assuming billing address country is used
            total_amount=Decimal(0),  # Initial amount is set to 0 and will be updated later
            currency_id=currency.id,
            tax=Decimal(tax),
            order_number=order_number,
            order_date=timezone.now(),
            order_note=order_note,
            ip=request.META.get('REMOTE_ADDR')
        )
        
        # Calculate the total amount based on cart items
        total_amount = Decimal(0)

        print(order.order_number)
        if page_location == "cart":
            order_items = []

            for cart_item in cart_items:
                product = cart_item.product
                product_price = get_object_or_404(ProductPrice, product=product, currencies=currency)
                unit_price = product_price.value
                subtotal = unit_price * cart_item.quantity
                total_amount += subtotal
                
                # Create order item
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=cart_item.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal
                )
                order_items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": cart_item.quantity,
                    "unit_price": str(unit_price),
                    "subtotal": str(subtotal)
                })
            order.checkout_type = 'cart'
        else:
            print('direct buy now')
            product_price = get_object_or_404(ProductPrice, product=product, currencies=currency)
            unit_price = product_price.value
            print(unit_price, 'kfjbdjfblkdjfblk')
            order.checkout_type = 'direct'
            
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=int('1'),
                unit_price=unit_price,
                subtotal=unit_price
            )
            total_amount += unit_price

        print(total_amount)
        # Apply discount if valid
        discount = Decimal(0)
        if discount_code:
            discount_obj = Coupon.objects.filter(code=discount_code, is_active=True).first()
            if discount_obj and discount_obj.valid_from <= timezone.now().date() <= discount_obj.valid_to:
                discount = Decimal(discount_obj.calculate_discount_amount(total_amount))

        # Update the order's total amount
        final_total = total_amount - discount
        order.total_amount = final_total
        order.discount_amount = discount
        order.save()

        # Create PayPal payment
        try:
            approval_url = create_paypal_payment(request, order.order_number)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare response data
        response_data = {
            "detail": "Order created successfully",
            "approval_url" : approval_url,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class GuestCheckoutAPIView(APIView):
    def post(self, request):
        data = request.data
        country_code = data.get('country_code', 'US')
        page_location = data.get('page_location')
        billing_data = request.data.get('billing_address', {})
        shipping_data = request.data.get('shipping_address', {})

        print("dfgdfgdfg")
        # Extract billing address details
        email = billing_data.get('email')
        first_name = billing_data.get('first_name')
        last_name = billing_data.get('last_name')

        billing_address_line_1 = billing_data.get('address_line_1')
        billing_address_line_2 = billing_data.get('address_line_2', '')
        billing_country_name = billing_data.get('country')
        billing_state_name = billing_data.get('state')
        billing_city_name = billing_data.get('city')
        billing_zip_code = billing_data.get('zip_code')
        billing_contact_person = billing_data.get('contact_person', f"{first_name} {last_name}")
        billing_contact_phone = billing_data.get('contact_phone', '')

        cart_id = request.data.get('cart_id')
        discount_code = request.data.get('discount_code')
        tax = request.data.get('tax')
        order_note = request.data.get('order_note')

        # Extract shipping address details (can be the same as billing)
        shipping_address_line_1 = shipping_data.get('address_line_1')
        shipping_address_line_2 = shipping_data.get('address_line_2', '')
        shipping_country_name = shipping_data.get('country')
        shipping_state_name = shipping_data.get('state')
        shipping_city_name = shipping_data.get('city')
        shipping_zip_code = shipping_data.get('zip_code')
        shipping_contact_person = shipping_data.get('contact_person', f"{first_name} {last_name}")
        shipping_contact_phone = shipping_data.get('contact_phone', '')

        print("dfgdfgdfg")
        # Create or get the guest user
        user, created = Account.objects.get_or_create(
            email=email,
            defaults={
                'phone_number': billing_contact_phone,
                'is_active': False
            }
        )
        print("dfgdfgdfg")
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'image': f"{current_url}media/profile_images/default.png",
                'country': billing_country_name
            }
        )

        if not created and user.is_active:
            return Response({"detail": "User already exists and is active. Please log in."}, status=status.HTTP_400_BAD_REQUEST)
        print("dfgdfgdfg")
        # Create billing address
        billing_country = get_object_or_404(Country, name=billing_country_name)
        billing_state = get_object_or_404(State, name=billing_state_name)
        billing_address = Address.objects.create(
            profile=profile,
            address_line_1=billing_address_line_1,
            address_line_2=billing_address_line_2,
            country=billing_country,
            state=billing_state,
            city=billing_city_name,
            zip_code=billing_zip_code,
            contact_person=billing_contact_person,
            contact_phone=billing_contact_phone,
            is_default=True
        )
        print("dfgdfgdfg")

        # Create shipping address (if different from billing)
        shipping_country = get_object_or_404(Country, name=shipping_country_name)
        shipping_state = get_object_or_404(State, name=shipping_state_name)
        
        shipping_address = Address.objects.create(
            profile=profile,
            address_line_1=shipping_address_line_1,
            address_line_2=shipping_address_line_2,
            country=shipping_country,
            state=shipping_state,
            city=shipping_city_name,
            zip_code=shipping_zip_code,
            contact_person=shipping_contact_person,
            contact_phone=shipping_contact_phone,
            is_default=False
        )
        print("sdfgdfg")

        currency = get_object_or_404(Currencies, countries__code=country_code)

        print("sdfgdfg")
        # Fetch cart items for guest user
        # cart = Cart.objects.get(cart_id=cart_id)
        # cart_items = CartItem.objects.filter(cart=cart)

        # if not cart_items.exists():
        #     return Response({"detail": "No items in cart to create an order."}, status=status.HTTP_400_BAD_REQUEST)

        current_datetime = timezone.now()
        year = current_datetime.strftime('%Y')
        month = current_datetime.strftime('%m')
        timestamp = int(current_datetime.timestamp())
        order_number = f"BA{month}{year}{timestamp}"


        # Create order
        order = Order.objects.create(
            user=user,
            billing_address=billing_address.id,
            shipping_address=shipping_address.id,
            country=billing_address.country.name,
            total_amount=Decimal(0),
            currency_id=currency.id,
            tax=Decimal(tax),
            order_number=order_number,
            order_date=timezone.now(),
            order_note=order_note,
            ip=request.META.get('REMOTE_ADDR')
        )

        total_amount = Decimal(0)
        order_items = []

        if page_location == "cart":
            # Fetch cart items
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart)  # Assuming CartItem is related to the user
            print('cart')
            # Check if cart is empty
            if not cart_items.exists():
                return Response({"detail": "No items in cart to create an order."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            sku = data.get('product_sku')
            print('no cart')
            product = Product.objects.get(sku=sku)

        if page_location == "cart":
            for cart_item in cart_items:
                product = cart_item.product
                product_price = get_object_or_404(ProductPrice, product=product, currencies=currency)
                unit_price = product_price.value
                subtotal = unit_price * cart_item.quantity
                total_amount += subtotal

                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=cart_item.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal
                )
                order_items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": cart_item.quantity,
                    "unit_price": str(unit_price),
                    "subtotal": str(subtotal)
                })
        else:
            print('direct buy now')
            product_price = get_object_or_404(ProductPrice, product=product, currencies=currency)
            unit_price = product_price.value
            print(unit_price, 'kfjbdjfblkdjfblk')
            order.checkout_type = 'direct'
            
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=int('1'),
                unit_price=unit_price,
                subtotal=unit_price
            )
            total_amount += unit_price

        discount = Decimal(0)
        if discount_code:
            discount_obj = Coupon.objects.filter(code=discount_code, is_active=True).first()
            if discount_obj and discount_obj.valid_from <= timezone.now().date() <= discount_obj.valid_to:
                discount = Decimal(discount_obj.calculate_discount_amount(total_amount))

        final_total = total_amount - discount
        order.total_amount = final_total
        order.discount_amount = discount
        order.save()

        try:
            approval_url = create_paypal_payment(request, order.order_number)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Fetch the "Order Placed" status
            order_placed_status = OrderStatus.objects.get(name="Order Placed")
            
            # Create the history entry
            OrderStatusHistory.objects.create(
                order=order,
                status=order_placed_status,
            )
            print("ho gaya")
        except OrderStatus.DoesNotExist:
            # Log or handle the error if "Order Placed" status is missing
            print("OrderStatus 'Order Placed' does not exist.")

        response_data = {
            "detail": "Order created successfully",
            "approval_url": approval_url,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)



