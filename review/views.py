from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import Review

class UserReviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Fetch all reviews submitted by the logged-in user
            reviews = Review.objects.get_query().filter(user=request.user, is_accepted = True)
            
            reviews_list = []
            for review in reviews:
                reviews_list.append({
                    'id': review.id,
                    'product': review.product.name,
                    'product_image': '',
                    'rating': review.rating,
                    'title_comment': review.title_comment,
                    'comment': review.comment,
                    'created_at': review.created_at.strftime('%m-%d-%Y  %H:%M'),
                })

            return JsonResponse({'reviews': reviews_list}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)