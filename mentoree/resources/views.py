"""
Views for the resources app.

This file defines ViewSets for managing resources via REST API.
Includes filtering, permissions, and download functionality.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.http import Http404
from django.core.mail import send_mail
from django.conf import settings

from .models import Category, Resource
from .serializers import (
    CategorySerializer, ResourceSerializer,
    CreateResourceSerializer, ValidateResourceSerializer
)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners or admins to access resources.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read access to validated resources for everyone
        if request.method in permissions.SAFE_METHODS and obj.status == 'validated':
            return True

        # Allow owners and admins full access
        return obj.created_by == request.user or request.user.is_staff


class ResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing resources.

    Endpoints:
    - GET /api/resources/ - List resources (filtered)
    - POST /api/resources/ - Create resource
    - GET /api/resources/{id}/ - Get resource detail
    - PATCH /api/resources/{id}/ - Update resource
    - DELETE /api/resources/{id}/ - Delete resource
    - PATCH /api/resources/{id}/validate/ - Validate/reject resource (admin only)
    - GET /api/resources/{id}/download/ - Download resource file
    """
    queryset = Resource.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'category', 'origin', 'difficulty', 'status']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'title', 'featured']
    ordering = ['-featured', '-created_at']

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return CreateResourceSerializer
        return ResourceSerializer

    def get_permissions(self):
        """
        Return permissions based on action.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['validate']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """
        Filter queryset based on user permissions and query parameters.
        """
        queryset = Resource.objects.all()

        # Filter by status for non-authenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='validated')

        # Additional filters from query params
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__icontains=q)
            )

        tags = self.request.query_params.get('tags')
        if tags:
            # Filter by tags (comma-separated)
            tag_list = [tag.strip() for tag in tags.split(',')]
            for tag in tag_list:
                queryset = queryset.filter(tags__icontains=tag)

        return queryset

    def perform_create(self, serializer):
        """
        Create resource and send notification to admins if pending.
        """
        resource = serializer.save()

        # Send email notification to admins for pending resources
        if resource.status == 'pending':
            self._notify_admins_new_resource(resource)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def validate(self, request, pk=None):
        """
        Validate or reject a resource (admin only).

        Updates status and sends notification to resource creator.
        """
        resource = self.get_object()
        serializer = ValidateResourceSerializer(data=request.data)

        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            comment = serializer.validated_data.get('comment', '')

            resource.status = new_status
            resource.save()

            # Send notification to creator
            self._notify_creator_validation(resource, comment)

            return Response({
                'message': f'Resource {new_status} successfully.',
                'resource': ResourceSerializer(resource, context={'request': request}).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download(self, request, pk=None):
        """
        Download resource file for authenticated users.
        """
        resource = self.get_object()

        # Check if resource has a file and user can access it
        if not resource.file:
            return Response(
                {'error': 'No file available for download.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only allow download for validated resources or resource owner/admin
        if resource.status != 'validated' and resource.created_by != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Access denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Return file URL
        file_url = request.build_absolute_uri(resource.file.url)
        return Response({
            'download_url': file_url,
            'filename': resource.file.name.split('/')[-1]
        })

    def _notify_admins_new_resource(self, resource):
        """
        Send email notification to admins about new pending resource.
        """
        subject = f'New Resource Pending Validation: {resource.title}'
        message = f"""
        A new resource has been submitted and requires validation.

        Title: {resource.title}
        Type: {resource.get_type_display()}
        Created by: {resource.created_by.username if resource.created_by else 'Anonymous'}

        Please review and validate/reject the resource in the admin panel.
        """

        # Send to all staff users (admins)
        admin_emails = [user.email for user in self.request.user.__class__.objects.filter(is_staff=True)]
        if admin_emails:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=True
            )

    def _notify_creator_validation(self, resource, comment):
        """
        Send email notification to resource creator about validation status.
        """
        if not resource.created_by or not resource.created_by.email:
            return

        subject = f'Your Resource "{resource.title}" has been {resource.get_status_display()}'
        message = f"""
        Your submitted resource has been reviewed.

        Title: {resource.title}
        Status: {resource.get_status_display()}
        """

        if comment:
            message += f"\nAdmin Comment: {comment}"

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [resource.created_by.email],
            fail_silently=True
        )


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for categories (read-only).

    Endpoints:
    - GET /api/categories/ - List all categories
    - GET /api/categories/{id}/ - Get category detail
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class FeaturedResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for featured resources.

    Endpoints:
    - GET /api/resources/featured/ - List featured resources
    """
    queryset = Resource.objects.filter(featured=True, status='validated')
    serializer_class = ResourceSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Return all featured resources


class ResourceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for resources filtered by type.

    Endpoints:
    - GET /api/resources/types/{type}/ - List resources of specific type
    """
    serializer_class = ResourceSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Filter resources by type from URL parameter.
        """
        resource_type = self.kwargs.get('type')
        if resource_type not in dict(Resource.RESOURCE_TYPES):
            raise Http404("Invalid resource type")

        queryset = Resource.objects.filter(type=resource_type, status='validated')

        # Apply same filtering as main ViewSet
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__icontains=q)
            )

        return queryset.order_by('-featured', '-created_at')
