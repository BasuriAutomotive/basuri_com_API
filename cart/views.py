from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated


from .models import Cart, CartItem
from product.models import Currencies, Product, ProductGallery, ProductPrice


class AddToCartAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        country_code = request.data.get('country_code', 'US')
        product_sku = request.data.get('product_sku')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(sku=product_sku)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        cart_item, created = CartItem.objects.get_query().get_or_create(user=user, product=product, defaults={'quantity': quantity})
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        data = {
            'product_name': cart_item.product.name, 
            'product_sku': cart_item.product.sku, 
            'product_image': '',  
            'quantity': cart_item.quantity, 
            'product_price' : ProductPrice.objects.filter(product_id=cart_item.product.id, currencies__countries__code=country_code).values('currencies__code', 'value', 'currencies__symbol').first()
            }

        return Response(data, status=status.HTTP_201_CREATED)


class ViewCartAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        country_code = request.data.get('country_code', 'US')
        currency = get_object_or_404(Currencies, countries__code=country_code)
        cart_items = CartItem.objects.get_query().filter(user=user, is_active=True)
        data = {
            'currency': currency.symbol,  # Root level currency field
            'products': [
                {
                    'product_name': item.product.name, 
                    'product_sku': item.product.sku, 
                    'product_image': ProductGallery.objects.filter(product=item.product, type="image").order_by('position').values_list('file', flat=True).first(),
                    'quantity': item.quantity, 
                    'product_price': ProductPrice.objects.filter(product_id=item.product.id, currencies__countries__code=country_code).values('currencies__code', 'value', 'currencies__symbol').first()
                } for item in cart_items
            ]
        }

        return Response(data)


class AddToCartNonAuthenticatedAPIView(APIView):
    def post(self, request):
        country_code = request.data.get('country_code', 'US')
        product_sku = request.data.get('product_sku')
        quantity = int(request.data.get('quantity', 1))
        cart_id = request.data.get('cart_id')

        try:
            product = Product.objects.get(sku=product_sku)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        if cart_id:
            cart, created = Cart.objects.get_or_create(cart_id=cart_id)
        else:
            cart = Cart.objects.create()

        cart_item, created = CartItem.objects.get_query().get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        data = {
            'product_name': cart_item.product.name, 
            'product_sku': cart_item.product.sku, 
            'product_image': '',  
            'quantity': cart_item.quantity, 
            'product_price' : ProductPrice.objects.filter(product_id=cart_item.product.id, currencies__countries__code=country_code).values('currencies__code', 'value', 'currencies__symbol').first()
            }

        return Response(data, status=status.HTTP_201_CREATED)


class ViewCartNonAuthenticatedAPIView(APIView):
    def get(self, request):
        country_code = request.data.get('country_code', 'US')
        currency = get_object_or_404(Currencies, countries__code=country_code)
        cart_id = request.query_params.get('cart_id')

        try:
            cart, create = Cart.objects.get_or_create(cart_id=cart_id)
        except Exception as e:
            return Response({'error': f'Cart not found {e}'}, status=status.HTTP_404_NOT_FOUND)

        cart_items = CartItem.objects.get_query().filter(cart=cart, is_active=True)

        data = {
            'currency': currency.symbol,
            'products': [
                {
                    'product_name': item.product.name, 
                    'product_sku': item.product.sku,  
                    'product_image': ProductGallery.objects.filter(product=item.product, type="image").order_by('position').values_list('file', flat=True).first(),
                    'quantity': item.quantity, 'product_price' : ProductPrice.objects.filter(product_id=item.product.id, currencies__countries__code=country_code).values('currencies__code', 'value', 'currencies__symbol').first()
                } for item in cart_items
            ]
        }

        return Response(data) 
    
class DecreaseCartItemAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        product_sku = request.data.get('product_sku')
        
        try:
            product = Product.objects.get(sku=product_sku)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            cart_item = CartItem.objects.get(product=product, user=request.user, is_active=True, is_deleted=False)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                return Response({
                    'quantity': cart_item.quantity,
                    'product_sku': product_sku
                }, status=status.HTTP_200_OK)
            else:
                cart_item.delete()
                return Response({
                    'message': 'Cart item deleted!',
                    'product_sku': product_sku
                }, status=status.HTTP_200_OK)
        except Exception as e:
           
            return Response({'message': 'An error occurred while updating the cart item'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class DecreaseCartItemNonAuthenticatedAPIView(APIView):
    def delete(self, request, cart_id):
        product_sku = request.data.get('product_sku')
        cart = Cart.objects.get(cart_id=cart_id)
        try:
            product = Product.objects.get(sku=product_sku)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product, is_active=True, is_deleted=False)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                return Response({
                    'quantity': cart_item.quantity,
                    'product_sku': product_sku
                }, status=status.HTTP_200_OK)
            else:
                cart_item.delete()
                return Response({
                    'message': 'Cart item deleted!',
                    'product_sku': product_sku
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'An error occurred while updating the cart item'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RemoveAllCartItemsAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        product_sku = request.data.get('product_sku')
        try:
            product = Product.objects.get(sku=product_sku)
            print(product_sku)
            cart_items = CartItem.objects.get_query().filter(user=user,product=product, is_active=True)
            if cart_items.count()>0:
                cart_items.delete()

                return Response({'message': 'All cart items removed successfully'}, status=status.HTTP_204_NO_CONTENT)
            return JsonResponse({'message': 'No such items Found in cart'}, status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({'error': 'Cart Item not exist'}, status=status.HTTP_404_NOT_FOUND)
        

class RemoveAllCartItemsNonAuthenticatedAPIView(APIView):
    def delete(self, request, cart_id):
        product_sku = request.data.get('product_sku')
        cart = Cart.objects.get(cart_id=cart_id)
        try:
            product = Product.objects.get(sku=product_sku)
            cart_items = CartItem.objects.filter(cart=cart, product=product, is_active=True)
            if cart_items.count()>0:
                cart_items.delete()

                return Response({'message': 'All cart items removed successfully'}, status=status.HTTP_204_NO_CONTENT)
            return JsonResponse({'message': 'No cart items Found'}, status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({'error': 'Cart Item not exist'}, status=status.HTTP_404_NOT_FOUND)