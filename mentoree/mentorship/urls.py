from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'goals', views.GoalViewSet)
router.register(r'sessions', views.SessionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/mentee/', views.dashboard_mentee, name='dashboard-mentee'),
    path('dashboard/mentor/', views.dashboard_mentor, name='dashboard-mentor'),
]