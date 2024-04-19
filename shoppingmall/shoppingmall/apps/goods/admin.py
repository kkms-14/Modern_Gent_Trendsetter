from django.contrib import admin
from .models import SKU, SPU


# Register your models here.

class SKUAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'cost_price', 'market_price', 'stock', 'sales',
                    'comments', 'is_launched']

    search_fields = ['name']
    list_editable = ['price', 'cost_price', 'market_price', 'stock', 'is_launched']


class SPUAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'sales']
    search_fields = ['name']


admin.site.register(SKU, SKUAdmin)
admin.site.register(SPU, SPUAdmin)
