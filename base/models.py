from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

def get_file_path(instance, filename):
    # Get file extension
    ext = filename.split('.')[-1].lower()
    # Define upload path based on file type
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
        return f'messages/images/{instance.user.username}/{filename}'
    elif ext in ['mp3', 'wav', 'ogg', 'm4a']:
        return f'messages/audio/{instance.user.username}/{filename}'
    elif ext in ['mp4', 'avi', 'mov', 'wmv', 'mkv']:
        return f'messages/video/{instance.user.username}/{filename}'
    else:
        return f'messages/documents/{instance.user.username}/{filename}'

class Topic(models.Model):
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name

class Room(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='participants', blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_participants = models.IntegerField(default=50)
    study_type = models.CharField(max_length=50, choices=[
        ('quiet', 'Quiet Study'),
        ('discussion', 'Discussion'),
        ('teaching', 'Teaching/Tutoring'),
    ], default='discussion')
    is_private = models.BooleanField(default=False)
    private_id = models.CharField(max_length=8, blank=True, null=True)
    private_password = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        ordering = ['-updated', '-created']
    
    def __str__(self):
        return self.name
    
    @property
    def participant_count(self):
        return self.participants.count()
    
    def get_participants_data(self):
        participants = self.participants.all()
        return [{
            'id': p.id,
            'username': p.username,
            'is_superuser': p.is_superuser
        } for p in participants]

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    body = models.TextField()
    file_attachment = models.FileField(upload_to=get_file_path, null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_type = models.CharField(max_length=20, blank=True, null=True)  # image, audio, video, document
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created']
    
    def __str__(self):
        return self.body[0:50]
    
    def save(self, *args, **kwargs):
        if self.file_attachment:
            # Set file name
            self.file_name = self.file_attachment.name
            
            # Determine file type based on extension
            ext = self.file_attachment.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                self.file_type = 'image'
            elif ext in ['mp3', 'wav', 'ogg', 'm4a']:
                self.file_type = 'audio'
            elif ext in ['mp4', 'avi', 'mov', 'wmv', 'mkv']:
                self.file_type = 'video'
            else:
                self.file_type = 'document'
        
        super().save(*args, **kwargs)

class Vote(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    VOTE_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=7, choices=VOTE_CHOICES)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'message')
    
    def __str__(self):
        return f"{self.user.username} {self.vote_type}d {self.message.body[:20]}"

class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    goal = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.room.name} - {self.start_time}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    study_streak = models.IntegerField(default=0)
    total_study_hours = models.FloatField(default=0)
    reputation_points = models.IntegerField(default=0)
    preferred_study_time = models.CharField(max_length=20, choices=[
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('night', 'Night'),
    ], blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    @property
    def total_likes_received(self):
        return Vote.objects.filter(message__user=self.user, vote_type='like').count()