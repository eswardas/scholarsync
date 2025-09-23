from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
    
    # Study room specific fields
    is_active = models.BooleanField(default=True)
    max_participants = models.IntegerField(default=50)
    study_type = models.CharField(max_length=50, choices=[
        ('quiet', 'Quiet Study'),
        ('discussion', 'Discussion'),
        ('teaching', 'Teaching/Tutoring'),
    ], default='discussion')
    
    class Meta:
        ordering = ['-updated', '-created']
    
    def __str__(self):
        return self.name
    
    @property
    def participant_count(self):
        return self.participants.count()

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    body = models.TextField()
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created']
    
    def __str__(self):
        return self.body[0:50]

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
        unique_together = ('user', 'message')  # One vote per user per message
    
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