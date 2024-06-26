from django.contrib import admin

from users.models import CustomUser


class UserAdmin(admin.ModelAdmin):
    """
    Админ-зона пользователя.
    """
    list_display = ('id', 'username', 'first_name', 'last_name', 'email')
    search_fields = ('email', 'username')
    list_filter = ('email', 'username')
    empty_value_display = '-пусто-'


admin.site.register(CustomUser, UserAdmin)
