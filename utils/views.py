from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import MenuItem

def build_menu_tree(menu_items):
    menu_dict = {}
    for item in menu_items:
        # Remove the specified string from the URL
        item['url'] = item['url'].replace('https://basuriautomotive.com', '')
        item['children'] = []
        menu_dict[item['id']] = item
    
    root_items = []
    for item in menu_items:
        if item['parent_id']:
            parent = menu_dict[item['parent_id']]
            parent['children'].append(item)
        else:
            root_items.append(item)
    
    return root_items

@method_decorator(csrf_exempt, name='dispatch')
class MenuItemListCreateView(View):
    def get(self, request):
        menu_items = MenuItem.objects.all().values().order_by('position')
        menu_tree = build_menu_tree(menu_items)
        return JsonResponse(menu_tree, safe=False)