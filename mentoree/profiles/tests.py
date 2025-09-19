import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import MentorProfile, MenteeProfile, MentorshipRequest
from .serializers import MentorProfileListSerializer, MentorshipRequestSerializer

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def mentor_user(db):
    return CustomUser.objects.create_user(
        username='mentor1',
        email='mentor1@example.com',
        password='password123',
        role='mentor'
    )

@pytest.fixture
def mentor_profile(db, mentor_user):
    return MentorProfile.objects.create(
        user=mentor_user,
        expertise=['Python', 'Django'],
        years_of_experience=5,
        location='Yaoundé'
    )

@pytest.fixture
def mentee_user(db):
    return CustomUser.objects.create_user(
        username='mentee1',
        email='mentee1@example.com',
        password='password123',
        role='mentee'
    )

@pytest.fixture
def mentee_profile(db, mentee_user):
    return MenteeProfile.objects.create(user=mentee_user)

@pytest.mark.django_db
def test_mentor_list(api_client, mentor_profile):
    url = reverse('mentor-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['user']['username'] == 'mentor1'

@pytest.mark.django_db
def test_mentor_detail(api_client, mentor_profile):
    url = reverse('mentor-detail', args=[mentor_profile.id])
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['user']['username'] == 'mentor1'
    assert response.data['expertise'] == ['Python', 'Django']

@pytest.mark.django_db
def test_create_mentorship_request(api_client, mentor_profile, mentee_user):
    api_client.force_authenticate(user=mentee_user)
    url = reverse('mentorship-request-list')
    data = {
        'mentor_id': mentor_profile.id,
        'message': 'I would like to learn more about Django.'
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert MentorshipRequest.objects.count() == 1
    request = MentorshipRequest.objects.first()
    assert request.mentor == mentor_profile
    assert request.mentee.user == mentee_user
    assert request.message == 'I would like to learn more about Django.'

@pytest.mark.django_db
def test_update_mentorship_request_status(api_client, mentor_profile, mentee_user):
    request = MentorshipRequest.objects.create(
        mentor=mentor_profile,
        mentee=mentee_profile,
        message='Test request'
    )
    api_client.force_authenticate(user=mentor_profile.user)
    url = reverse('mentorship-request-update-status', args=[request.id])
    data = {'status': 'accepted'}
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_200_OK
    request.refresh_from_db()
    assert request.status == 'accepted'
