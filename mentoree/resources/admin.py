"""
Admin configuration for the resources app.

This file registers Resource and Category models in Django admin
with custom filters and display options.
"""

from django.contrib import admin
from .models import Category, Resource


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin for Category model.

    Allows managing resource categories with slug auto-generation.
    """
    list_display = ['name', 'slug']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """
    Admin for Resource model.

    Provides comprehensive management of resources with filtering and validation.
    """
    list_display = [
        'title', 'type', 'status', 'origin', 'difficulty',
        'featured', 'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'type', 'origin', 'difficulty', 'featured',
        'category', 'created_at'
    ]
    search_fields = ['title', 'description', 'tags', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    ordering = ['-featured', '-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'type', 'category')
        }),
        ('Content', {
            'fields': ('url', 'file')
        }),
        ('Metadata', {
            'fields': ('source', 'origin', 'difficulty', 'tags', 'featured')
        }),
        ('Status & Permissions', {
            'fields': ('status', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset for admin list view.
        """
        return super().get_queryset(request).select_related('category', 'created_by')

    def save_model(self, request, obj, form, change):
        """
        Set created_by on creation if not set.
        """
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['mark_as_validated', 'mark_as_rejected', 'mark_as_featured']

    @admin.action(description='Mark selected resources as validated')
    def mark_as_validated(self, request, queryset):
        """
        Bulk action to validate selected resources.
        """
        updated = queryset.update(status='validated')
        self.message_user(
            request,
            f'{updated} resource(s) marked as validated.'
        )

    @admin.action(description='Mark selected resources as rejected')
    def mark_as_rejected(self, request, queryset):
        """
        Bulk action to reject selected resources.
        """
        updated = queryset.update(status='rejected')
        self.message_user(
            request,
            f'{updated} resource(s) marked as rejected.'
        )

    @admin.action(description='Mark selected resources as featured')
    def mark_as_featured(self, request, queryset):
        """
        Bulk action to feature selected resources.
        """
        updated = queryset.update(featured=True)
        self.message_user(
            request,
            f'{updated} resource(s) marked as featured.'
        )
