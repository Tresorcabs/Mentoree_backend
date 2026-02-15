from django.contrib import admin
from .models import Conversation, Message, Task, UserStatus


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'mentor', 'mentee', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['mentor__user__username', 'mentee__user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_preview', 'message_type', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'created_at']
    search_fields = ['sender__username', 'content']
    readonly_fields = ['created_at', 'read_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if obj.content and len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'title', 'assigned_by', 'assigned_to', 'status', 'priority', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'assigned_by__username', 'assigned_to__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']


@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_online', 'last_seen', 'current_room']
    list_filter = ['is_online', 'last_seen']
    search_fields = ['user__username']
    readonly_fields = ['last_seen']
