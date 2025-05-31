from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import User
from django.contrib.auth.models import Group

class UserAdmin(admin.ModelAdmin):
    model = User
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone_number', 'gender', 'action_buttons')
    list_filter = ('email',)
    search_fields = ('email', 'phone_number')
    ordering = ('-id',)
    list_per_page = 10

    def action_buttons(self, obj):
        edit_url = reverse('admin:users_user_change', args=[obj.id])
        delete_url = reverse('admin:users_user_delete', args=[obj.id])
        return format_html(
            '<a class="button" href="{}">Edit</a> | <a class="button" href="{}">Delete</a>',
            edit_url, delete_url
        )
    action_buttons.short_description = 'Actions'

admin.site.register(User, UserAdmin)

admin.site.unregister(Group)