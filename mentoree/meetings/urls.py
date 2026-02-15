from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_meeting, name='create_meeting'),
    path('user/', views.get_user_meetings, name='get_user_meetings'),
    path('<int:meeting_id>/', views.get_meeting, name='get_meeting'),
    path('<int:meeting_id>/start/', views.start_meeting, name='start_meeting'),
    path('<int:meeting_id>/end/', views.end_meeting, name='end_meeting'),
    path('<int:meeting_id>/recordings/', views.get_meeting_recordings, name='get_meeting_recordings'),
]