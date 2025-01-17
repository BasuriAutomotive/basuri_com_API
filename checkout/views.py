import stripe
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from order.models import Order, OrderItem, OrderStatus, OrderStatusHistory
from payment.views import create_payment_intent, create_paypal_payment
from product.models import Currencies, Product, ProductPrice
from cart.models import Cart, CartItem
from discount.models import Coupon
from accounts.models import Account, Profile
from address.models import Address, Country, State
from django.utils import timezone
from decimal import Decimal
from django.conf import settings

current_url = settings.CURRENT_URL
stripe.api_key = settings.STRIPE_SECRET_KEY

class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data
        user = request.user if request.user.is_authenticated else None
        
        # Extracting order details
        country_code = request.query_params.get('country_code', 'US')
        # Try to fetch the currency based on the given country code
        currency = Currencies.objects.filter(countries__code=country_code).first()
        # If no currency is found, default to the US currency
        if not currency:
            currency = get_object_or_404(Currencies, countries__code='US')

        page_location = data.get('page_location')
        billing_address_id = data.get('billing_address')
        shipping_address_id = data.get('shipping_address')
        same_address = data.get('isShippingAddressIsSameAsBilling')
        discount_code = data.get('discount_code')
        # currency_code = data.get('currency')
        # tax = data.get('tax')
        order_note = data.get('order_note')
        payment_type = data.get('payment_type')
        
        # Fetching Address instances
        billing_address = get_object_or_404(Address, id=billing_address_id)
        if same_address == "true":
            shipping_address = billing_address
        else:
            shipping_address = get_object_or_404(Address, id=shipping_address_id)

        subtotal=Decimal(0)
       
        if page_location == "cart":
            # Fetch cart items
            cart_items = CartItem.objects.filter(user=user)  # Assuming CartItem is related to the user
            # Check if cart is empty
            if not cart_items.exists():
                return Response({"detail": "No items in cart to create an order."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            sku = data.get('product_sku')
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
            order_number=order_number,
            order_date=timezone.now(),
        )

        try:
            order.ip = data.get('ip_address')
            order.order_note=order_note
            order.payment_type = payment_type
            order.save()
        except:
            pass

        # Calculate the total amount based on cart items
        total_amount = Decimal(0)

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
            product_price = get_object_or_404(ProductPrice, product=product, currencies=currency)
            unit_price = product_price.value
            order.checkout_type = 'direct'
            
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=int('1'),
                unit_price=unit_price,
                subtotal=unit_price
            )
            total_amount += unit_price

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

        # # Create PayPal payment
        # try:
        #     approval_url = create_paypal_payment(request, order.order_number)
        # except Exception as e:
        #     return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # # Prepare response data
        # response_data = {
        #     "detail": "Order created successfully",
        #     "approval_url" : approval_url,
        # }

        # return Response(response_data, status=status.HTTP_201_CREATED)

        if payment_type == "paypal":
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
            except:
                pass

            response_data = {
                "detail": "Order created successfully",
                "approval_url": approval_url,
            }

        elif payment_type == "stripe":

            try:
                amount = int(Decimal(order.total_amount) * 100)
                print(amount)
                currency = currency.code
                lowercase_currency = currency.lower()
                print(lowercase_currency)
                client_secret = create_payment_intent(request, amount, lowercase_currency, order.id)
            except:
                return Response("Stripe Not Working", status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Fetch the "Order Placed" status
                order_placed_status = OrderStatus.objects.get(name="Order Placed")
                
                # Create the history entry
                OrderStatusHistory.objects.create(
                    order=order,
                    status=order_placed_status,
                )
            except:
                pass
            
            response_data = {
                "detail": "Order created successfully",
                "client_secret": client_secret,
            }

        elif payment_type == "credit_card":

            try:
                amount = int(Decimal(order.total_amount) * 100)
                print(amount)
                currency = currency.code
                lowercase_currency = currency.lower()
                print(lowercase_currency)
                client_secret = create_payment_intent(request, amount, lowercase_currency, order.id)
            except:
                return Response("Card Not Working", status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Fetch the "Order Placed" status
                order_placed_status = OrderStatus.objects.get(name="Order Placed")
                
                # Create the history entry
                OrderStatusHistory.objects.create(
                    order=order,
                    status=order_placed_status,
                )
            except:
                pass
            
            response_data = {
                "detail": "Order created successfully",
                "client_secret": client_secret,
            }

        return Response(response_data, status=status.HTTP_201_CREATED)


class GuestCheckoutAPIView(APIView):
    def post(self, request):
        data = request.data
        country_code = request.query_params.get('country_code', 'US')
        # Try to fetch the currency based on the given country code
        currency = Currencies.objects.filter(countries__code=country_code).first()
        # If no currency is found, default to the US currency
        if not currency:
            currency = get_object_or_404(Currencies, countries__code='US')
        page_location = data.get('page_location')
        billing_data = data.get('billing_address', {})
        same_address = data.get('isShippingAddressIsSameAsBilling')
        shipping_data = data.get('shipping_address', {})

        # Extract billing address details
        email = billing_data.get('email')
        email = email.lower()
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

        cart_id = data.get('cart_id')
        discount_code = data.get('discount_code')
        # tax = data.get('tax')
        order_note = data.get('order_note')
        payment_type = data.get('payment_type')

        # Create or get the guest user
        user, created = Account.objects.get_or_create(
            email=email,
            defaults={
                'phone_number': billing_contact_phone,
                'is_active': False
            }
        )

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

        if same_address == "true":
            shipping_address_id = billing_address.id

        else :

            # Extract shipping address details (can be the same as billing)
            shipping_address_line_1 = shipping_data.get('address_line_1')
            shipping_address_line_2 = shipping_data.get('address_line_2', '')
            shipping_country_name = shipping_data.get('country')
            shipping_state_name = shipping_data.get('state')
            shipping_city_name = shipping_data.get('city')
            shipping_zip_code = shipping_data.get('zip_code')
            shipping_contact_person = shipping_data.get('contact_person', f"{first_name} {last_name}")
            shipping_contact_phone = shipping_data.get('contact_phone', '')

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

            shipping_address_id = shipping_address.id


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
            shipping_address=shipping_address_id,
            country=billing_address.country.name,
            total_amount=Decimal(0),
            currency_id=currency.id,
            order_number=order_number,
            order_date=timezone.now(),
        )

        try:
            order.ip = data.get('ip_address')
            order.order_note=order_note
            order.payment_type = payment_type
            order.save()
        except:
            pass

        total_amount = Decimal(0)
        order_items = []

        if page_location == "cart":
            # Fetch cart items
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart)  # Assuming CartItem is related to the user
            # Check if cart is empty
            if not cart_items.exists():
                return Response({"detail": "No items in cart to create an order."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            sku = data.get('product_sku')
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
            product_price = get_object_or_404(ProductPrice, product=product, currencies=currency)
            unit_price = product_price.value
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

        if payment_type == "paypal":
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
            except:
                pass

            response_data = {
                "detail": "Order created successfully",
                "approval_url": approval_url,
            }

        elif payment_type == "stripe":

            try:
                amount = int(Decimal(order.total_amount) * 100)
                print(amount)
                currency = currency.code
                lowercase_currency = currency.lower()
                print(lowercase_currency)
                client_secret = create_payment_intent(request, amount, lowercase_currency, order.id)
            except:
                return Response("Stripe Not Working", status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Fetch the "Order Placed" status
                order_placed_status = OrderStatus.objects.get(name="Order Placed")
                
                # Create the history entry
                OrderStatusHistory.objects.create(
                    order=order,
                    status=order_placed_status,
                )
            except:
                pass
            
            response_data = {
                "detail": "Order created successfully",
                "client_secret": client_secret,
            }

        elif payment_type == "credit_card":

            try:
                amount = int(Decimal(order.total_amount) * 100)
                print(amount)
                currency = currency.code
                lowercase_currency = currency.lower()
                print(lowercase_currency)
                client_secret = create_payment_intent(request, amount, lowercase_currency, order.id)
            except:
                return Response("Card Not Working", status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Fetch the "Order Placed" status
                order_placed_status = OrderStatus.objects.get(name="Order Placed")
                
                # Create the history entry
                OrderStatusHistory.objects.create(
                    order=order,
                    status=order_placed_status,
                )
            except:
                pass
            
            response_data = {
                "detail": "Order created successfully",
                "client_secret": client_secret,
            }

        return Response(response_data, status=status.HTTP_201_CREATED)