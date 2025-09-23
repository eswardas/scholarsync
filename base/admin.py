from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Room, Topic, Message, Vote, StudySession, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, )

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'topic', 'participant_count', 'created']
    list_filter = ['topic', 'study_type', 'created']
    search_fields = ['name', 'description', 'host__username']
    readonly_fields = ['updated', 'created']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'body_preview', 'created']
    list_filter = ['created', 'room__topic']
    search_fields = ['body', 'user__username', 'room__name']
    readonly_fields = ['updated', 'created']
    
    def body_preview(self, obj):
        return obj.body[:50] + "..." if len(obj.body) > 50 else obj.body
    body_preview.short_description = 'Message Preview'

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'created']
    list_filter = ['created']
    search_fields = ['user__username']

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'start_time', 'end_time', 'completed']
    list_filter = ['completed', 'start_time']
    search_fields = ['user__username', 'room__name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_study_time', 'study_streak', 'total_study_hours', 'reputation_points']
    list_filter = ['preferred_study_time']
    search_fields = ['user__username', 'bio']