from django.contrib import admin
from orders.models import OrderInfo


# Register your models here.

class OrderInfoAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'total_amount', 'total_amount', 'freight', 'pay_method', 'status']
    search_fields = ['order_id']
    list_editable = ['freight', 'status']


admin.site.register(OrderInfo, OrderInfoAdmin)
