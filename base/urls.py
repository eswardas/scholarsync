# base/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # The new landing page is now the root URL
    path('', views.landingPage, name='landing'),
    
    # The old home page is now at '/rooms/' and is the main dashboard for logged-in users
    path('rooms/', views.home, name='home'),
    
    path('room/<int:pk>/', views.room, name='room'),
    path('room/<int:pk>/data/', views.get_room_data, name='room-data'),
    path('vote/<int:pk>/', views.voteMessage, name='vote-message'),
    path('delete-message/<int:pk>/', views.deleteMessage, name='delete-message'),
    path('report/<int:pk>/', views.reportMessage, name='report-message'),
    path('create-room/', views.createRoom, name='create-room'),
    path('update-room/<int:pk>/', views.updateRoom, name='update-room'),
    path('delete-room/<int:pk>/', views.deleteRoom, name='delete-room'),
    path('topics/', views.topicsPage, name='topics'),
    path('activity/', views.activityPage, name='activity'),

    # --- FIX: ADD THIS LINE FOR LIVE ACTIVITY DATA ---
    path('activity/data/', views.get_activity_data, name='activity-data'),

    path('join-private-room/', views.joinPrivateRoom, name='join-private-room'),
    path('private-room-info/', views.privateRoomInfo, name='private-room-info'),
    path('profile/<int:pk>/', views.userProfile, name='user-profile'),
    path('update-user/', views.updateUser, name='update-user'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('register/', views.registerPage, name='register'),

    # Admin moderation pages
    path('moderation/reports/', views.admin_reports, name='moderation-reports'),
    path('moderation/reports/<int:report_id>/action/', views.admin_report_action, name='moderation-report-action'),
]