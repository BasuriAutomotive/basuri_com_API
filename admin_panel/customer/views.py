from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import Account
from accounts.permissions import IsStaff


class CustomerListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, request):
        
        # Fetch accounts with the role of 'customer'
        customers = Account.objects.filter(role='customer').select_related('profile')

        # Build the response data
        customer_data = []
        for sr_no, customer in enumerate(customers, start=0):
            # Check if the profile exists for the customer
            profile = getattr(customer, 'profile', None)
            
            if profile:
                customer_data.append({
                    "id": sr_no,
                    "email": customer.email,
                    "phone_number": customer.phone_number,
                    # "first_name": profile.first_name,
                    # "last_name": profile.last_name,
                    "full_name": profile.first_name + ' ' +  profile.last_name,
                    "image": profile.image,
                    "country": profile.country,
                    "phone_code": profile.phone_code,
                    "is_active": customer.is_active,
                    "role": customer.role
                })
            # else:
            #     # Handle accounts with no profile by setting profile fields to None
            #     customer_data.append({
            #         "id": customer.id,
            #         "email": customer.email,
            #         "phone_number": customer.phone_number,
            #         "full_name": "Profile Not found!",
            #         # "first_name": None,
            #         # "last_name": None,
            #         "image": None,
            #         "country": None,
            #         "phone_code": None,
            #         "is_active": customer.is_active,
            #         "role": customer.role
            #     })

        return Response(customer_data)