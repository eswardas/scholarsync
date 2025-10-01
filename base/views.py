from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from .models import Room, Topic, Message, Vote, StudySession, UserProfile
from .forms import SignUpForm, RoomForm, MessageForm, UserProfileForm, UserForm
from django.utils import timezone
import random
import string

@login_required(login_url='login')
def home(request):
    topic_q = request.GET.get('topic_q') if request.GET.get('topic_q') != None else ''
    name_q = request.GET.get('name_q') if request.GET.get('name_q') != None else ''
    
    # Filter rooms based on search parameters
    rooms = Room.objects.filter(is_private=False)  # Only show public rooms
    
    if topic_q:
        rooms = rooms.filter(topic__name__icontains=topic_q)
    if name_q:
        rooms = rooms.filter(name__icontains=name_q)
    
    # Get topics without blank names
    topics = Topic.objects.exclude(name='').all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter()[0:5]
    
    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count,
        'room_messages': room_messages,
    }
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = get_object_or_404(Room, id=pk)
    
    # Check if room is private and user is not a participant
    if room.is_private and request.user not in room.participants.all() and request.user != room.host:
        return redirect('join-private-room')
    
    room_messages = room.message_set.all().prefetch_related('votes')
    participants = room.participants.all()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Handle file upload
        file_attachment = request.FILES.get('file_attachment')
        file_name = None
        file_type = None
        
        if file_attachment:
            file_name = file_attachment.name
            ext = file_name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                file_type = 'image'
            elif ext in ['mp3', 'wav', 'ogg', 'm4a']:
                file_type = 'audio'
            elif ext in ['mp4', 'avi', 'mov', 'wmv', 'mkv']:
                file_type = 'video'
            else:
                file_type = 'document'
        
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body', ''),
            file_attachment=file_attachment,
            file_name=file_name,
            file_type=file_type
        )
        room.participants.add(request.user)
        
        active_session = StudySession.objects.filter(
            user=request.user,
            room=room,
            end_time__isnull=True
        ).first()
        
        if not active_session:
            StudySession.objects.create(
                user=request.user,
                room=room
            )
        
        return redirect('room', pk=room.id)
    
    for message in room_messages:
        if request.user.is_authenticated:
            user_vote = Vote.objects.filter(user=request.user, message=message).first()
            message.user_vote = user_vote
        else:
            message.user_vote = None
    
    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants,
    }
    return render(request, 'base/room.html', context)

@login_required(login_url='login')
def get_room_data(request, pk):
    room = get_object_or_404(Room, id=pk)
    last_message_id = request.GET.get('last_id', 0)
    
    # Get new messages
    new_messages = Message.objects.filter(
        room=room,
        id__gt=last_message_id
    ).select_related('user').prefetch_related('votes')
    
    messages_data = []
    for msg in new_messages:
        user_vote = None
        if request.user.is_authenticated:
            vote_obj = Vote.objects.filter(user=request.user, message=msg).first()
            if vote_obj:
                user_vote = vote_obj.vote_type
        
        file_attachment_url = None
        if msg.file_attachment:
            file_attachment_url = msg.file_attachment.url
        
        messages_data.append({
            'id': msg.id,
            'username': msg.user.username,
            'user_id': msg.user.id,
            'body': msg.body,
            'created': msg.created.isoformat(),
            'like_count': msg.votes.filter(vote_type='like').count(),
            'dislike_count': msg.votes.filter(vote_type='dislike').count(),
            'user_vote': user_vote,
            'is_owner': msg.user == request.user,
            'is_admin': request.user.is_superuser,
            'file_attachment': file_attachment_url,
            'file_name': msg.file_name,
            'file_type': msg.file_type,
        })
    
    # Get current participants
    participants_data = room.get_participants_data()
    
    return JsonResponse({
        'messages': messages_data,
        'participants': participants_data,
        'last_id': new_messages.last().id if new_messages.exists() else last_message_id
    })

def userProfile(request, pk):
    user = get_object_or_404(User, id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()[0:5]
    topics = Topic.objects.exclude(name='').all()
    
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    total_likes = Vote.objects.filter(message__user=user, vote_type='like').count()
    
    context = {
        'user': user,
        'rooms': rooms,
        'room_messages': room_messages,
        'topics': topics,
        'profile': profile,
        'total_likes': total_likes,
    }
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.exclude(name='').all()
    
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        if topic_name and topic_name.strip() and topic_name != 'new':
            topic, created = Topic.objects.get_or_create(name=topic_name.strip())
        else:
            topic = None
        
        is_private = request.POST.get('is_private') == 'on'
        private_id = None
        private_password = None
        
        if is_private:
            # Generate unique ID (8 characters)
            private_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            # Generate password (6 characters)
            private_password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        
        room = Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            study_type=request.POST.get('study_type'),
            max_participants=request.POST.get('max_participants'),
            is_private=is_private,
            private_id=private_id,
            private_password=private_password
        )
        
        # Add host as participant
        room.participants.add(request.user)
        
        if is_private:
            # Redirect to private room info page
            return render(request, 'base/private_room_info.html', {'room': room})
        else:
            return redirect('home')
    
    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = get_object_or_404(Room, id=pk)
    
    if request.user != room.host:
        return HttpResponse('You are not allowed here!')
    
    form = RoomForm(instance=room)
    
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        if topic_name and topic_name.strip() and topic_name != 'new':
            topic, created = Topic.objects.get_or_create(name=topic_name.strip())
            room.topic = topic
        elif topic_name == 'new':
            # Handle new topic creation if needed
            pass
        
        room.name = request.POST.get('name')
        room.description = request.POST.get('description')
        room.study_type = request.POST.get('study_type')
        room.max_participants = request.POST.get('max_participants')
        room.save()
        return redirect('home')
    
    context = {'form': form, 'room': room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = get_object_or_404(Room, id=pk)
    
    if request.user != room.host:
        return HttpResponse('You are not allowed here!')
    
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    
    return render(request, 'base/delete.html', {'obj': room})

@login_required(login_url='login')
def deleteMessage(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    message = get_object_or_404(Message, id=pk)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.user != message.user and not request.user.is_superuser:
        return JsonResponse({'error': 'You are not allowed here!'}, status=403)
    
    message.delete()
    return JsonResponse({'status': 'success'})

@login_required(login_url='login')
def voteMessage(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    message = get_object_or_404(Message, id=pk)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.user == message.user:
        return JsonResponse({'error': 'You cannot vote on your own message'}, status=400)
    
    vote_type = request.POST.get('vote_type')
    
    if vote_type not in ['like', 'dislike']:
        return JsonResponse({'error': 'Invalid vote type'}, status=400)
    
    vote, created = Vote.objects.get_or_create(
        user=request.user,
        message=message,
        defaults={'vote_type': vote_type}
    )
    
    if not created:
        if vote.vote_type == vote_type:
            vote.delete()
            action = 'removed'
        else:
            vote.vote_type = vote_type
            vote.save()
            action = 'changed'
    else:
        action = 'added'
    
    like_count = message.votes.filter(vote_type='like').count()
    dislike_count = message.votes.filter(vote_type='dislike').count()
    
    return JsonResponse({
        'action': action,
        'vote_type': vote_type if action != 'removed' else None,
        'like_count': like_count,
        'dislike_count': dislike_count,
    })

def loginPage(request):
    page = 'login'
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist.')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exist.')
    
    context = {'page': page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('login')

def registerPage(request):
    form = SignUpForm()
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            
            UserProfile.objects.get_or_create(user=user)
            
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')
    
    return render(request, 'base/login_register.html', {'form': form})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    form = UserForm(instance=user)
    profile_form = UserProfileForm(instance=profile)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            return redirect('user-profile', pk=user.id)
    
    return render(request, 'base/update-user.html', {
        'form': form,
        'profile_form': profile_form
    })

@login_required(login_url='login')
def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.exclude(name='').filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})

@login_required(login_url='login')
def activityPage(request):
    room_messages = Message.objects.all()[0:5]
    return render(request, 'base/activity.html', {'room_messages': room_messages})

@login_required(login_url='login')
def joinPrivateRoom(request):
    error_message = None
    
    if request.method == 'POST':
        private_id = request.POST.get('private_id')
        private_password = request.POST.get('private_password')
        
        try:
            room = Room.objects.get(private_id=private_id, private_password=private_password, is_private=True)
            
            # Add user to participants
            room.participants.add(request.user)
            
            return redirect('room', pk=room.id)
        except Room.DoesNotExist:
            error_message = "Invalid room ID or password. Please try again."
    
    return render(request, 'base/join_private_room.html', {'error_message': error_message})

@login_required(login_url='login')
def privateRoomInfo(request):
    # This view is called after creating a private room
    # It should display the private room details
    return render(request, 'base/private_room_info.html')