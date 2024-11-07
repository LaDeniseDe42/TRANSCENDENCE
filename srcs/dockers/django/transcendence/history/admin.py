from django.contrib import admin

# Register your models here.
from .models import History  # Assurez-vous d'importer votre modèle History

class HistoryAdmin(admin.ModelAdmin):
    list_display = ('game', 'mode', 'winner', 'scoreW', 'scoreL', 'looser', 'date' , 'name')
    search_fields = ('game', 'mode', 'winner__username', 'looser__username')
    
admin.site.register(History, HistoryAdmin)
admin.site.site_header = 'Transcendence'
admin.site.site_title = 'Transcendence'