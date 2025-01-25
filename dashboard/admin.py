from django.contrib import admin
from .models import App, AppLog

@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'status', 'created_at', 'updated_at')
    list_filter = ('type', 'status')
    search_fields = ('name', 'path', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AppLog)
class AppLogAdmin(admin.ModelAdmin):
    list_display = ('app', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('app__name', 'action', 'details')
    readonly_fields = ('timestamp',)
