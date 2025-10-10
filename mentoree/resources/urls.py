"""
URL configuration for the resources app.

This file defines URL patterns for resource-related endpoints.
Routes are included under /api/resources/ in the main URL configuration.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register ViewSets
router = DefaultRouter()
router.register(r'', views.ResourceViewSet, basename='resource')
router.register(r'categories', views.CategoryViewSet, basename='category')

# Custom URL patterns
custom_patterns = [
    path('featured/', views.FeaturedResourceViewSet.as_view({'get': 'list'}), name='featured-resources'),
    path('types/<str:type>/', views.ResourceTypeViewSet.as_view({'get': 'list'}), name='resource-type-list'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('', include(custom_patterns)),
]