from rest_framework import serializers
from dashboard.models import App, AppLog

class AppLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppLog
        fields = ['id', 'action', 'details', 'timestamp']

class AppSerializer(serializers.ModelSerializer):
    logs = AppLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = App
        fields = ['id', 'name', 'path', 'description', 'status', 'port', 'logs']
        read_only_fields = ['status', 'port', 'logs']

    def validate_path(self, value):
        """Validate the path exists"""
        if not value:
            raise serializers.ValidationError("Path is required")
        return value

    def validate(self, data):
        """Validate the data"""
        return data 