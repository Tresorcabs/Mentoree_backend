from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'tasks', views.TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    path('user-status/', views.user_status_detail, name='user-status-detail'),
    path('user-status/list/', views.user_status_list, name='user-status-list'),
    path('unread-count/', views.unread_messages_count, name='unread-messages-count'),
    path('conversations/<int:conversation_id>/mark-read/', views.mark_messages_read, name='mark-messages-read'),
]