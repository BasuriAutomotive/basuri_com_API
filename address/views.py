import random
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated

from accounts.models import Profile
from address.models import Country, State, Address

class UserAddressAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the authenticated user
        user = request.user
        
        # Get the profile associated with the user
        profile = get_object_or_404(Profile, user=user)
        
        # Get all addresses associated with the profile
        addresses = Address.objects.get_query().filter(profile=profile)
        
        # Check if no addresses are found
        if not addresses.exists():
            return Response([], status=status.HTTP_200_OK)
        
        # Prepare the response data in the desired format
        data = [
            {
                "id": address.id,
                "contact_person": address.contact_person,
                "contact_phone": address.contact_phone,
                "street": address.address_line_1,
                "street2": address.address_line_2,
                "city": address.city if address.city else "",
                "state_name": address.state.name if address.state else "",
                "country_name": address.country.name if address.country else "",
                "zip": address.zip_code
            }
            for address in addresses
        ]
        
        return Response(data, status=status.HTTP_200_OK)
    
    def post(self, request):
        # Get the authenticated user
        user = request.user
        
        # Get the profile associated with the user
        profile = get_object_or_404(Profile, user=user)
        
        # Get data from the request
        contact_person = request.data.get('contact_person')
        address_line_1 = request.data.get('street')
        address_line_2 = request.data.get('street2', '')
        city_name = request.data.get('city')
        zip_code = request.data.get('zip')
        state_name = request.data.get('state_name')
        country_name = request.data.get('country_name')
        contact_phone = request.data.get('contact_phone')
        
        # Validate the presence of required data
        if not all([contact_person, address_line_1, city_name, zip_code, state_name, country_name, contact_phone]):
            return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create the country
        country = Country.objects.filter(name=country_name).first()
        if not country:
            return Response({'error': 'Country not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create the state
        state = State.objects.filter(name=state_name, country=country).first()
        if not state:
            return Response({'error': 'State not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        
        # Create a new address
        address = Address.objects.create(
            profile=profile,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            country=country,
            state=state,
            city=city_name,
            zip_code=zip_code,
            contact_person=contact_person,
            contact_phone=contact_phone
        )
        
        # Prepare the response data in the desired format
        data = {
            "id": address.id,
            "contact_person": address.contact_person,
            "street": address.address_line_1,
            "street2": address.address_line_2,
            "city": address.city if address.city else "",
            "zip": address.zip_code,
            "state_name": address.state.name if address.state else "",
            "country_name": address.country.name if address.country else "",
            "contact_phone": address.contact_phone
        }
        
        return Response(data, status=status.HTTP_201_CREATED)
    
    def delete(self, request):
        # Get the authenticated user
        user = request.user
        
        # Get the profile associated with the user
        profile = get_object_or_404(Profile, user=user)
        
        # Get the address ID from the request data
        address_id = request.data.get('address_id')
        
        if not address_id:
            return Response({'error': 'Address ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the address associated with the profile and the provided address ID
            address = Address.objects.get(id=address_id, profile=profile)
            address.is_deleted = True
            address.save()
            return Response({'message': 'Address deleted successfully'}, status=status.HTTP_200_OK)
        except Address.DoesNotExist:
            return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
        


class CountryWithStatesListAPIView(APIView):
    def get(self, request):
        countries = Country.objects.all()
        country_list = []
        
        for country in countries:
            states = State.objects.filter(country=country)
            state_list = [
                {
                    "name": state.name,
                    "code": state.code
                }
                for state in states
            ]
            
            flag_url = f"{settings.STATIC_URL}country/{country.code.lower()}.png"
            flag_url = request.build_absolute_uri(flag_url)

            country_data = {
                "flag": flag_url,
                "name": country.name,
                "code": country.code,
                "currency": country.currency,
                "states": state_list
            }
            
            country_list.append(country_data)
        
        return Response(country_list, status=status.HTTP_200_OK)
