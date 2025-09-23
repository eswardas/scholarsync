from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from .models import Room, Topic, Message, Vote, StudySession, UserProfile
from .forms import SignUpForm, RoomForm, MessageForm, UserProfileForm, UserForm

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))[0:5]
    
    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count,
        'room_messages': room_messages,
    }
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = get_object_or_404(Room, id=pk)
    room_messages = room.message_set.all().prefetch_related('votes')
    participants = room.participants.all()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
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
    
    # Annotate each message with current user's vote (if any)
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

def userProfile(request, pk):
    user = get_object_or_404(User, id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()[0:5]
    topics = Topic.objects.all()
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Calculate total likes received (only 'like' votes count)
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
    topics = Topic.objects.all()
    
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            study_type=request.POST.get('study_type'),
            max_participants=request.POST.get('max_participants')
        )
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
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
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
    message = get_object_or_404(Message, id=pk)
    
    if request.user != message.user:
        return JsonResponse({'error': 'You are not allowed here!'}, status=403)
    
    if request.method == 'POST':
        message.delete()
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'POST method required'}, status=405)

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
    return redirect('home')

def registerPage(request):
    form = SignUpForm()
    
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            
            # Create user profile automatically
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
def voteMessage(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    message = get_object_or_404(Message, id=pk)
    
    # CSRF already handled by middleware since we're using Django templates
    # But double-check user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.user == message.user:
        return JsonResponse({'error': 'You cannot vote on your own message'}, status=400)
    
    vote_type = request.POST.get('vote_type')
    
    if vote_type not in ['like', 'dislike']:
        return JsonResponse({'error': 'Invalid vote type'}, status=400)
    
    # Get or create vote
    vote, created = Vote.objects.get_or_create(
        user=request.user,
        message=message,
        defaults={'vote_type': vote_type}
    )
    
    if not created:
        # Already voted - toggle or switch
        if vote.vote_type == vote_type:
            # Remove vote
            vote.delete()
            action = 'removed'
        else:
            # Switch vote type
            vote.vote_type = vote_type
            vote.save()
            action = 'changed'
    else:
        action = 'added'
    
    # Get updated counts
    like_count = message.votes.filter(vote_type='like').count()
    dislike_count = message.votes.filter(vote_type='dislike').count()
    
    return JsonResponse({
        'action': action,
        'vote_type': vote_type if action != 'removed' else None,
        'like_count': like_count,
        'dislike_count': dislike_count,
    })
def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})

def activityPage(request):
    room_messages = Message.objects.all()[0:5]
    return render(request, 'base/activity.html', {'room_messages': room_messages})