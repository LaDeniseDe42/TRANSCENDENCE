from django.contrib import admin
from .models import myUser
# Register your models here.


class myUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'date_joined', 'is_active', 'is_staff', 'is_admin', 'is_superuser', 'intra_id')
    search_fields = ('username', 'email', 'date_joined', 'is_active', 'is_staff', 'is_admin', 'is_superuser', 'intra_id')
    readonly_fields = ('date_joined',)

admin.site.register(myUser, myUserAdmin)
admin.site.site_header = 'Transcendence'
admin.site.site_title = 'Transcendence'