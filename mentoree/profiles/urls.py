from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'mentors', views.MentorViewSet, basename='mentor')
router.register(r'mentorship-requests', views.MentorshipRequestViewSet, basename='mentorship-request')
router.register(r'reviews', views.MentorReviewViewSet, basename='review')
router.register(r'mentees', views.MenteeProfileViewSet, basename='mentee')

urlpatterns = [
    path('', include(router.urls)),
    path('mentor-profile/update/', views.update_mentor_profile, name='update-mentor-profile'),
    path('mentee-profile/update/', views.update_mentee_profile, name='update-mentee-profile'),
]

# API Endpoints created:
# /api/profiles/mentors/ - List all mentors (GET)
# /api/profiles/mentors/{id}/ - Get mentor details (GET)
# /api/profiles/mentors/{id}/toggle_favorite/ - Toggle favorite status (POST)
# /api/profiles/mentorship-requests/ - List/Create requests (GET, POST)
# /api/profiles/mentorship-requests/{id}/ - Get/Update/Delete request (GET, PUT, DELETE)
# /api/profiles/mentorship-requests/{id}/update_status/ - Update request status (POST)
# /api/profiles/mentorship-requests/mentor_requests/ - Get all requests for current mentor (GET)
# /api/profiles/mentorship-requests/{id}/send_message/ - Send message to mentee (POST)
# /api/profiles/reviews/ - List/Create reviews (GET, POST)
# /api/profiles/reviews/{id}/ - Get/Update/Delete review (GET, PUT, DELETE)
# /api/profiles/mentees/ - List mentees (GET)
# /api/profiles/mentees/{id}/ - Get mentee details (GET)