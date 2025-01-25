from rest_framework import serializers
from dashboard.models import App, AppLog

class AppLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppLog
        fields = ['id', 'action', 'timestamp', 'details']

class AppSerializer(serializers.ModelSerializer):
    logs = AppLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = App
        fields = ['id', 'name', 'path', 'type', 'status', 'description', 'created_at', 'updated_at', 'logs'] 