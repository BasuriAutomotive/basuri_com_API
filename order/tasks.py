import requests
from decouple import config
from celery import shared_task, chain

from address.models import Address, Country
from .models import Order, OrderAction


# ERP ORDER GENERATE
@shared_task(name='erp_order')
def create_erp_order_task(order_number):
    try:
        # Retrieve the order
        order = Order.objects.get(order_number=order_number)
        
        # Get or create the OrderAction for ERP
        action, created = OrderAction.objects.get_or_create(
            order=order,
            action_name="CREATE_ERP",
        )

        # If the action is already successful, skip further processing
        if not created and action.status == 'SUCCESS':
            return "ERP order already created successfully."

        # Reset the action status to PENDING for retries
        action.status = 'PENDING'
        action.details = None  # Clear previous details if any
        action.save()

        # Perform the ERP order creation task
        task_chain = chain(
            get_token.s(),
            create_order.s(order_number),
        )()
        so_number = task_chain.get()


        return so_number

    except Exception as e:
        # Handle the exception gracefully and update the action status
        error_message = f"An error occurred during ERP order creation: {e}"
        if 'action' in locals():
            action.status = 'FAILED'
            action.details = error_message
            action.save()

        return error_message


# GET TOKEN FROM ERP
@shared_task
def get_token():
    api_url = config('TOKEN_API_URL')
    username = 'info@basuriautomotive.com'
    password = config('PASSWORD')
    if username is None or password is None:
        return None
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(api_url, data=data)
    if response.status_code == 200:
        token = response.json().get('access')
        return token
    else:
        return None


# CREATE ORDER IN ERP
@shared_task
def create_order(token, order_number):
    order = Order.objects.get(order_number=order_number)

    # Get or create the OrderAction for ERP
    action, created = OrderAction.objects.get_or_create(
        order=order,
        action_name="CREATE_ERP",
    )

    api_url = config('ORDER_API_URL')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    shipping_address = Address.objects.get(id=int(order.shipping_address))
    billing_address = Address.objects.get(id=int(order.billing_address))
    data = {
        "part_no": [],
        "qty": [],
        "order_no": order.order_number,
        "remarks": f'''
        Customer           : {order.user.profile.first_name} {order.user.profile.last_name}
        Email              : {order.user.email}
        Phone              : {order.user.phone_number}
        Shipping_Address   : {shipping_address.address_line_1}, {shipping_address.address_line_2} 
        Shipping_State     : {shipping_address.state}
        Shipping_City      : {shipping_address.city}
        Shipping_Country   : {shipping_address.country} 
        Shipping_Zip Code  : {shipping_address.zip_code} 
        Billing_Address    : {billing_address.address_line_1}, {billing_address.address_line_2} 
        Billing_State      : {billing_address.state}
        Billing_City       : {billing_address.city},
        Billing_Country    : {shipping_address.country} 
        Billing_Zip Code   : {billing_address.zip_code}
        Payment            : {order.payment_id}
        TotalAmount        : {order.currency.symbol}{order.total_amount}'''
    }
    country = order.country
    country = Country.objects.get(name=country)
    sku_code=country.continents

    for i in order.items.all():
        if i.product.category.name == "Basuri Air Horns":
            data["part_no"].append(sku_code + i.product.sku)
            data["qty"].append(i.quantity)
        else:
            data["part_no"].append(i.product.sku)
            data["qty"].append(i.quantity)

    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        order_data = response.json()
        so_number = order_data.get('order_no')
        order.so_number = so_number
        order.save()
        
        # Update the action status to SUCCESS upon completion
        action.status = 'SUCCESS'
        action.details = f"ERP order created successfully. SO Number: {so_number}"
        action.save()
        
        return so_number
    else:
        action.status = 'FAILED'
        action.details = None
        action.save()
        return None
    
# SEND ORDER NOTIFICATION
# @shared_task
# def send_alert_celery(order_number):
#     url = "https://www.smsalert.co.in/api/push.json?order_number="+order_number+'&apikey=62419f63427a9'+'&sender=OCWEBS'+'&mobileno=9104515704&text=A+new+order+has+been+placed+on+BasuriAutomotive.+Please+review+the+details:%0D%0A%0D%0AOrder+Number:++'+order_number+'%0D%0A%0D%0AKindly+ensure+timely+processing+and+fulfillment+of+the+order.%0D%0A%0D%0AThank+you%2C%0D%0AZIYA+FAB'
#     payload = {}
#     headers= {}
#     response = requests.request("POST", url, headers=headers, data = payload)
#     return None

# @shared_task
# def order_auto_update():
#     orders = Order.objects.filter(is_active=True, is_paid=True).exclude(order_status='Deliverd')
#     for order in orders:
#         # Make a GET request to the API endpoint
#         api_url = f"https://erp.krunalindustries.com/dhl/{order.so_number}/track-order/"
#         try:
#             response = requests.get(api_url)
#             if response.status_code == 200:
#                 data = response.json()
#                 events = data.get('data', [])
#                 if events:
#                     latest_event = events[-1]
#                     current_event = latest_event.get('Event', '').lower()
#                     if current_event == 'delivered':
#                         try:
#                             fetch_order = Order.objects.get(id=order.id)
#                             fetch_order.order_status = 'Deliverd'
#                             fetch_order.save()
#                         except Order.DoesNotExist:
#                             pass
#         except:
#             pass
            
#     return None     