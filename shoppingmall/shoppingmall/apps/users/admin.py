from django.contrib import admin
from users.models import User


# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'mobile', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login']
    search_fields = ['username', 'mobile']
    list_editable = ['mobile', 'is_active']


admin.site.register(User, UserAdmin)
