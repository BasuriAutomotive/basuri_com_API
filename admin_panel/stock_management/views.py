from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from product.models import Product
from accounts.permissions import IsStaff


class ProductStockListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, request):
        products = Product.objects.values('id', 'name', 'stock_quantity')
        stock_data = list(products)  # Convert queryset to a list of dictionaries
        return Response({"products": stock_data})
    
    
class ProductStockUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def post(self, request):
        
        try:
            data = request.data
            product_id = data.get('product_id')
            quantity = data.get('quantity')
            action = data.get('action')  # "add" or "remove"

            if not all([product_id, quantity, action]):
                return Response({"error": "Missing required fields"}, status=400)

            # Fetch the product
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=404)

            # Update stock based on action
            if action == "add":
                product.stock_quantity += quantity
                product.save()
                message = f"Stock increased by {quantity}. New stock: {product.stock_quantity}"

            elif action == "remove":
                if product.stock_quantity < quantity:
                    return Response({"error": "Insufficient stock to remove"}, status=400)
                product.stock_quantity -= quantity
                product.save()
                message = f"Stock decreased by {quantity}. New stock: {product.stock_quantity}"

            else:
                return Response({"error": "Invalid action. Use 'add' or 'remove'."}, status=400)

            return Response({
                "product_id": product.id,
                "product_name": product.name,
                "new_stock_quantity": product.stock_quantity,
                "message": message
            }, status=200)


        except :
            return Response('Invalid Formet in API Body', status=400)
    


