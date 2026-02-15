from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from users.models import CustomUser
from .models import Sprint, Task
from .serializers import (
    SprintSerializer, SprintCreateSerializer,
    TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer
)


class SprintViewSet(viewsets.ModelViewSet):
    queryset = Sprint.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SprintCreateSerializer
        return SprintSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'mentor':
            return Sprint.objects.filter(mentor=user)
        elif user.role == 'mentee':
            return Sprint.objects.filter(mentee=user)
        return Sprint.objects.none()

    @action(detail=True, methods=['get'])
    def sprint_tasks(self, request, pk=None):
        sprint = self.get_object()
        tasks = sprint.tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'mentor':
            return Task.objects.filter(sprint__mentor=user)
        elif user.role == 'mentee':
            return Task.objects.filter(sprint__mentee=user)
        return Task.objects.none()

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        user = request.user

        # Mentor can update any task in their sprints
        if user.role == 'mentor' and instance.sprint.mentor == user:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)

        # Mentee can only update status of tasks in their sprints
        elif user.role == 'mentee' and instance.sprint.mentee == user:
            # Only allow status updates
            allowed_fields = {'status'}
            data = {k: v for k, v in request.data.items() if k in allowed_fields}
            if data:
                serializer = self.get_serializer(instance, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data)
            else:
                return Response({"detail": "Mentees can only update task status."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "You do not have permission to update this task."}, status=status.HTTP_403_FORBIDDEN)
