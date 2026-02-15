"""
Serializers for the resources app.

This file defines serializers for Category and Resource models.
Includes validation logic for resource creation and download URLs.
"""

from rest_framework import serializers
from .models import Category, Resource


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.

    Used for listing categories and associating resources with categories.
    """

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class ResourceSerializer(serializers.ModelSerializer):
    """
    Serializer for Resource model.

    Includes computed field 'download_url' for file downloads.
    Handles permissions for file access.
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False)
    created_by = serializers.StringRelatedField(read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'description', 'type', 'url', 'file', 'category',
            'category_id', 'source', 'origin', 'difficulty', 'tags',
            'content', 'summary', 'keypoints', 'duration',
            'created_by', 'status', 'featured', 'created_at', 'updated_at',
            'download_url'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_download_url(self, obj):
        """
        Generate download URL for file resources.

        Only returns URL if user is authenticated and resource has a file.
        """
        request = self.context.get('request')
        if obj.file and request and request.user.is_authenticated:
            return request.build_absolute_uri(obj.file.url)
        return None


class CreateResourceSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new resources.

    Includes validation logic for required fields based on resource type.
    Sets status to 'pending' for non-staff users.
    """
    category_id = serializers.IntegerField(required=False)

    class Meta:
        model = Resource
        fields = [
            'title', 'description', 'type', 'url', 'file', 'category_id',
            'source', 'origin', 'difficulty', 'tags', 'content', 'summary',
            'keypoints', 'duration', 'featured'
        ]

    def validate(self, data):
        """
        Validate resource creation data.

        Ensures required fields are present based on resource type:
        - Videos require URL
        - PDFs/Templates require either URL or file
        """
        resource_type = data.get('type')
        url = data.get('url')
        file = data.get('file')

        if resource_type == 'video' and not url:
            raise serializers.ValidationError({
                'url': 'URL is required for video resources.'
            })

        if resource_type in ['pdf', 'template'] and not (url or file):
            raise serializers.ValidationError({
                'url': 'Either URL or file is required for PDF/Template resources.'
            })

        return data

    def create(self, validated_data):
        """
        Create resource with proper status based on user permissions.

        Staff users can create validated resources directly.
        Non-staff users create pending resources.
        """
        request = self.context.get('request')
        if request and request.user.is_staff:
            validated_data['status'] = 'validated'
        else:
            validated_data['status'] = 'pending'

        validated_data['created_by'] = request.user if request else None

        # Handle category association
        category_id = validated_data.pop('category_id', None)
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({
                    'category_id': 'Invalid category ID.'
                })

        return super().create(validated_data)


class ValidateResourceSerializer(serializers.Serializer):
    """
    Serializer for validating/rejecting resources.

    Used by admin endpoints to change resource status.
    """
    status = serializers.ChoiceField(choices=['validated', 'rejected'])
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate_status(self, value):
        """
        Validate status transition.

        Only allow validated or rejected status.
        """
        if value not in ['validated', 'rejected']:
            raise serializers.ValidationError(
                "Status must be either 'validated' or 'rejected'."
            )
        return value