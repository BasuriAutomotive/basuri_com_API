from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.db.models import Q

from review.models import Review
from utils.models import Currencies
from .models import Category, Product, ProductGallery, ProductPrice
from django.conf import settings

current_url = settings.CURRENT_URL

class CategoryView(View):
    def get(self, request, slug):
        # Fetch category based on slug, ensure the category is not deleted
        category = Category.objects.get(slug=slug, is_deleted=False)

        # Get country code from the request, default to 'US'
        country_code = request.GET.get('country_code', 'US')

        # Fetch products related to the category, using get_query() if available
        products = Product.objects.get_query().filter(category__slug=slug)

        # Prepare the product list with prices
        product_list = []
        for product in products:
            # Fetch price for the product based on country code or default to 'US'
            product_price = ProductPrice.objects.filter(
                product=product, currencies__countries__code=country_code
            ).values('currencies__code', 'value', 'currencies__symbol').first()

            if not product_price:
                # Fallback to 'US' currency code if no price found for the country
                product_price = ProductPrice.objects.filter(
                    product=product, currencies__countries__code='US'
                ).values('currencies__code', 'value', 'currencies__symbol').first()

            # Construct the product dictionary
            product_dict = {
                'category': product.category.name,
                'category_slug': product.category.slug,
                'name': product.name.title(),
                'slug': f"/{product.category.slug}/{product.slug}",
                'image': '',  # Assuming you'd fill this with image URLs or paths
                'prices': product_price
            }
            product_list.append(product_dict)

        # Prepare the final response data
        response = {
            'title': category.name.title(),
            "meta_title": category.meta_title,
            'meta_description': category.meta_description,
            'products': product_list
        }

        # Return the response as JSON
        return JsonResponse(response, safe=False)

class ProductListView(View):
    def get(self, request):
        products = Product.objects.get_query()
        country_code = request.GET.get('country_code', 'US')

        product_list = []
        for product in products:
            # Find product price by country code, fallback to 'US' if not found
            product_price = product.productprice_set.filter(
                currencies__countries__code=country_code
            ).values('currencies__code', 'value', 'currencies__symbol').first()

            if not product_price:
                product_price = product.productprice_set.filter(
                    currencies__countries__code='US'
                ).values('currencies__code', 'value', 'currencies__symbol').first()

            product_dict = {
                'category': product.category.name,
                'category_slug': product.category.slug,
                'name': product.name.title(),
                'slug': "/" + product.category.slug + "/" + product.slug,
                'image': '',  # Assuming you'll add image logic here
                'prices': product_price
            }
            product_list.append(product_dict)

        return JsonResponse(product_list, safe=False)

class ProductDetailsView(View):
    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        product_files = ProductGallery.objects.filter(product=product).order_by('position').values('type', 'file', 'name')
        
        country_code = request.GET.get('country_code', 'US')
        
        # Add the main product image first
        images=[]

        images_data = {
            'original': current_url + 'media/products/images/HK631/1.webp/',
            'thumbnail': current_url + 'media/products/images/HK631/1.webp/'
        }
        images.append(images_data)

        product_price = ProductPrice.objects.filter(
            product_id=product.id, currencies__countries__code=country_code
        ).values('currencies__code', 'value', 'currencies__symbol').first()

        if not product_price:
                product_price = ProductPrice.objects.filter(
                    product_id=product.id, 
                    currencies__countries__code='US'
                ).values('currencies__code', 'value', 'currencies__symbol').first()


        if product_price:
            discount_percentage = 10
            price = int(product_price['value'])
            sale_price = float(price)
            total_price = round(sale_price / (1 - discount_percentage / 100))
            product_price['value'] = int(product_price['value'])

        # Organize files by type
        files_dict = {
            'AUDIO_TUNE': [],
            'ICON_DESC': [],
            'KEY_ICON': [],
            'INSIDE_BOX': [],
            'A_PLUS': [],
        }

        for file_obj in product_files:
            file_type = file_obj['type']
            if file_type in files_dict:
                files_dict[file_type].append({
                    'file': file_obj['file'],
                    'name': file_obj['name'].title()
                })

        # Fetch reviews for the product
        reviews = Review.objects.filter(product=product, is_accepted=True).values(
            'user__email', 'user__profile__first_name', 'user__profile__last_name', 'user__profile__image',  'rating', 'title_comment', 'comment'
        )

        # Rename the keys in the reviews
        renamed_reviews = [
            {
                'user_email': review['user__email'],
                'user_name': review['user__profile__first_name'] + ' ' + review['user__profile__last_name'],
                'user_image': review['user__profile__image'],
                'user_rating': review['rating'],
                'review_title': review['title_comment'],
                'review_comment': review['comment']
            }
            for review in reviews
        ]

        

        product_dict = {
            'category': product.category.name,
            'name': product.name.title(),
            'slug': product.slug,
            'sku' : product.sku,
            'description': product.description,
            'is_available': product.is_available,
            'stock_quantity': product.stock_quantity,
            'total' : total_price,
            'price': product_price,
            'files': files_dict,
            'reviews': renamed_reviews,
            'images' : images
        }

        return JsonResponse(product_dict, safe=False)
    

    
class ProductSearchAPIView(View):
    def get(self, request): 
        
        # Filter products by name containing the query string, case-insensitive
        # products = Product.objects.filter(name__icontains=query).select_related('category')[:10]

        products=[]
        queryset = Product.objects.all()
        # Get the search parameter from the request
        
        country_code = request.GET.get('country_code', 'US')

        search = request.GET.get('q','')
        if search:
                # Filter the queryset by multiple fields
                products = queryset.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search) |
                    Q(slug__icontains=search) 
        
                )
        
        product_list = []
        for product in products:
            # Ensure product is not None
            if product:
                product_price = ProductPrice.objects.filter(
                    product_id=product.id,
                    currencies__countries__code=country_code
                ).values('currencies__code', 'value', 'currencies__symbol').first()

                if not product_price:
                    product_price = ProductPrice.objects.filter(
                        product_id=product.id,
                        currencies__countries__code='US'
                    ).values('currencies__code', 'value', 'currencies__symbol').first()

                # Construct the product dictionary
                product_dict = {
                    # 'category': product.category.name,
                    # 'category_slug': product.category.slug,
                    'name': product.name.title(),
                    'slug': f"/{product.category.slug}/{product.slug}",
                    'image': current_url + 'media/products/images/HK631/1.webp/',
                    'prices': product_price if product_price else None
                }
                product_list.append(product_dict)

        if product_list:

            response = {
                'products': product_list
            }
            
            return JsonResponse(response, safe=False)
        else:
            return HttpResponse(status=404)