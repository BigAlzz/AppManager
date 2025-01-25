from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppViewSet, app_output, check_requirements

router = DefaultRouter()
router.register(r'apps', AppViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('apps/<int:app_id>/output/', app_output, name='app_output'),
    path('apps/<int:app_id>/check_requirements/', check_requirements, name='check_requirements'),
] 