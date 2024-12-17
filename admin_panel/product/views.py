from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from product.models import Product, ProductGallery
from accounts.permissions import IsStaff


class ProductListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, request):

        # Fetch all available products, including related category, gallery, and price information
        products = Product.objects.select_related('category').prefetch_related('product_gallery', 'productprice_set')

        # Build the response data
        product_data = []
        for product in products:
            # Fetch category details
            category = product.category
            category_data = {
                "name": category.name,
                "slug": category.slug,
            } if category else None

            # Differentiate gallery items based on specific types
            gallery_data = {
                "INSIDE_BOX": [],
                "KEY_ICON": [],
                "ICON_DESC": [],
                "A_PLUS": [],
                "AUDIO_TUNE": []
            }

            for gallery_item in product.product_gallery.all():
                item_data = {
                    "name": gallery_item.name,
                    "file": gallery_item.file,
                    "position": gallery_item.position,
                    "alt": gallery_item.alt,
                }

                # Append gallery items based on their type
                if gallery_item.type == "INSIDE_BOX":
                    gallery_data["INSIDE_BOX"].append(item_data)
                elif gallery_item.type == "KEY_ICON":
                    gallery_data["KEY_ICON"].append(item_data)
                elif gallery_item.type == "ICON_DESC":
                    gallery_data["ICON_DESC"].append(item_data)
                elif gallery_item.type == "A_PLUS":
                    gallery_data["A_PLUS"].append(item_data)
                elif gallery_item.type == "AUDIO_TUNE":
                    gallery_data["AUDIO_TUNE"].append(item_data)

            # Fetch product prices
            price_data = [
                {
                    "currency": price.currencies.code,
                    "value": str(price.value)
                }
                for price in product.productprice_set.all()
            ]

            first_image = ProductGallery.objects.filter(product=product, type="image").order_by('position').first()
            image_url = first_image.file if first_image else None

            # Append each product's details to the response list
            product_data.append({
                "id": product.id,
                "created_at": product.updated_at,
                "name": product.name,
                "sku": product.sku,
                "image": image_url,
                "vendor": product.vendor,
                "slug": product.slug,
                "description": product.description,
                "is_available": product.is_available,
                "stock_quantity": product.stock_quantity,
                "category": category_data,
                "gallery": gallery_data,
                "prices": price_data,
            })

        return Response(product_data)