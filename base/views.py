# base/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import (
    Room, Topic, Message, Vote, StudySession, UserProfile, MessageReport
)
from .forms import SignUpForm, RoomForm, MessageForm, UserProfileForm, UserForm

import random
import string

from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q

# NEW VIEW FOR THE LANDING PAGE
def landingPage(request):
    """
    Renders the beautiful startup/landing page for non-authenticated users.
    Redirects authenticated users to the main rooms dashboard.
    """
    if request.user.is_authenticated:
        return redirect('home') # Redirect logged-in users to the main dashboard
    return render(request, 'base/landing.html')


@user_passes_test(lambda u: u.is_superuser, login_url='login')
def admin_reports(request):
    """
    Simple moderation dashboard for message reports.
    Superusers only.
    """
    status = request.GET.get('status', 'open')  # open | reviewed | all
    q = request.GET.get('q', '').strip()

    reports = MessageReport.objects.select_related(
        'reporter', 'message__user', 'message__room'
    ).order_by('-created')

    if status in ('open', 'reviewed'):
        reports = reports.filter(status=status)

    if q:
        reports = reports.filter(
            Q(message__body__icontains=q) |
            Q(reporter__username__icontains=q) |
            Q(message__user__username__icontains=q) |
            Q(message__room__name__icontains=q)
        )

    paginator = Paginator(reports, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    counts = {
        'open': MessageReport.objects.filter(status='open').count(),
        'reviewed': MessageReport.objects.filter(status='reviewed').count(),
        'all': MessageReport.objects.all().count()
    }

    return render(request, 'base/admin_reports.html', {
        'page_obj': page_obj,
        'status': status,
        'q': q,
        'counts': counts,
    })


@require_POST
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def admin_report_action(request, report_id):
    """
    POST action handler for a report:
      - action=resolve            -> mark report reviewed
      - action=delete_message     -> delete the reported message (and mark reviewed)
      - action=suspend_user       -> suspend the author for N days
      - action=ban_user           -> delete the author's account
      - action=reopen             -> set status back to open
    """
    action = request.POST.get('action')
    report = get_object_or_404(MessageReport, id=report_id)

    if action == 'resolve':
        report.status = 'reviewed'
        report.save()
        messages.success(request, f"Report #{report.id} marked as reviewed.")
        return JsonResponse({'status': 'ok', 'message': 'Report resolved.'})

    elif action == 'delete_message':
        if not report.message:
            return JsonResponse({'error': 'Message already deleted.'}, status=400)
        msg = report.message
        msg_id = msg.id
        msg.delete()
        report.status = 'reviewed'
        report.save()
        messages.success(request, f"Message #{msg_id} deleted and report reviewed.")
        return JsonResponse({'status': 'ok', 'deleted_message_id': msg_id, 'new_status': report.status})

    elif action == 'suspend_user':
        if not report.message:
            return JsonResponse({'error': 'Cannot suspend user, message is deleted.'}, status=400)
        
        try:
            days = int(request.POST.get('days', 0))
            if days <= 0:
                return JsonResponse({'error': 'Suspension days must be a positive number.'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid number of days provided.'}, status=400)

        author = report.message.user
        profile, created = UserProfile.objects.get_or_create(user=author)
        
        suspension_end_date = timezone.now() + timedelta(days=days)
        profile.suspended_until = suspension_end_date
        profile.save()
        
        report.status = 'reviewed'
        report.save()
        messages.success(request, f"User '{author.username}' has been suspended for {days} day(s).")
        return JsonResponse({'status': 'ok', 'suspended_user_id': author.id, 'days': days})

    elif action == 'ban_user':
        if not report.message:
            return JsonResponse({'error': 'Cannot ban user, message is deleted.'}, status=400)
        
        author = report.message.user
        author_username = author.username
        
        author.delete()
        
        report.status = 'reviewed'
        report.save()
        messages.success(request, f"User '{author_username}' has been banned (account deleted).")
        return JsonResponse({'status': 'ok', 'banned_user': author_username})

    elif action == 'reopen':
        report.status = 'open'
        report.save()
        messages.info(request, f"Report #{report.id} has been reopened.")
        return JsonResponse({'status': 'ok', 'new_status': report.status})

    return JsonResponse({'error': 'Invalid action'}, status=400)


# The 'home' view now acts as the dashboard for logged-in users
@login_required(login_url='login')
def home(request):
    topic_q = request.GET.get('topic_q') if request.GET.get('topic_q') is not None else ''
    name_q = request.GET.get('name_q') if request.GET.get('name_q') is not None else ''

    rooms = Room.objects.filter(is_private=False)

    if topic_q:
        rooms = rooms.filter(topic__name__icontains=topic_q)
    if name_q:
        rooms = rooms.filter(name__icontains=name_q)

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

    if room.is_private and request.user not in room.participants.all() and request.user != room.host:
        return redirect('join-private-room')

    if request.user.is_authenticated:
        if not room.participants.filter(id=request.user.id).exists():
            if room.participants.count() < room.max_participants:
                room.participants.add(request.user)

    room_messages = room.message_set.select_related('user', 'parent__user').prefetch_related('votes')
    participants = room.participants.all()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')

        file_attachment = request.FILES.get('file_attachment')
        
        parent = None
        parent_id = request.POST.get('parent_id')
        if parent_id:
            parent = Message.objects.filter(id=parent_id, room=room).first()

        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body', ''),
            file_attachment=file_attachment,
            parent=parent
        )
        room.participants.add(request.user)

        active_session = StudySession.objects.filter(
            user=request.user,
            room=room,
            end_time__isnull=True
        ).first()
        if not active_session:
            StudySession.objects.create(user=request.user, room=room)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message_id': message.id,
                'parent_id': message.parent_id,
                'parent_username': message.parent.user.username if message.parent else None,
                'parent_excerpt': (message.parent.body[:80] + ('...' if len(message.parent.body) > 80 else '')) if message.parent else None,
            })

        return redirect('room', pk=room.id)

    for m in room_messages:
        m.user_vote = Vote.objects.filter(user=request.user, message=m).first() if request.user.is_authenticated else None

    return render(request, 'base/room.html', {
        'room': room,
        'room_messages': room_messages,
        'participants': participants,
    })

@login_required(login_url='login')
def get_room_data(request, pk):
    room = get_object_or_404(Room, id=pk)
    last_message_id = request.GET.get('last_id', 0)

    new_messages = Message.objects.filter(
        room=room,
        id__gt=last_message_id
    ).select_related('user', 'parent__user').prefetch_related('votes')

    messages_data = []
    for msg in new_messages:
        user_vote = None
        if request.user.is_authenticated:
            vote_obj = Vote.objects.filter(user=request.user, message=msg).first()
            if vote_obj:
                user_vote = vote_obj.vote_type

        file_attachment_url = msg.file_attachment.url if msg.file_attachment else None

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
            'parent_id': msg.parent_id,
            'parent_username': msg.parent.user.username if msg.parent else None,
            'parent_excerpt': (msg.parent.body[:80] + ('...' if len(msg.parent.body) > 80 else '')) if msg.parent else None,
        })

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
            private_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
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

        room.participants.add(request.user)

        if is_private:
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
@require_POST
def deleteMessage(request, pk):
    message = get_object_or_404(Message, id=pk)

    if request.user != message.user and not request.user.is_superuser:
        return JsonResponse({'error': 'You are not allowed here!'}, status=403)

    message_id = message.id
    message.delete()

    return JsonResponse({
        'status': 'success',
        'message_id': message_id
    })


@login_required(login_url='login')
@require_POST
def voteMessage(request, pk):
    message = get_object_or_404(Message, id=pk)

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


@login_required(login_url='login')
@require_POST
def reportMessage(request, pk):
    message = get_object_or_404(Message, id=pk)
    reason = request.POST.get('reason')
    details = request.POST.get('details', '')
    valid_reasons = {key for key, _ in MessageReport.REASONS}
    if reason not in valid_reasons:
        return JsonResponse({'error': 'Invalid reason'}, status=400)

    report, created = MessageReport.objects.update_or_create(
        reporter=request.user,
        message=message,
        defaults={
            'reason': reason,
            'details': details,
            'status': 'open'
        }
    )
    return JsonResponse({'status': 'ok', 'created': created})


def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = (request.POST.get('username') or '').lower()
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                profile = user.userprofile
                if profile.is_suspended:
                    remaining_time = profile.suspended_until - timezone.now()
                    days_left = remaining_time.days
                    
                    if days_left > 0:
                        suspension_message = f"Your account is suspended. You can log in after {days_left + 1} day(s)."
                    else:
                        hours_left = remaining_time.seconds // 3600
                        suspension_message = f"Your account is suspended. You can log in after approximately {hours_left + 1} hour(s)."
                    
                    messages.error(request, suspension_message)
                    return redirect('login')
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user)
            
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('landing') # Redirect to the new landing page


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
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
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
            room.participants.add(request.user)
            return redirect('room', pk=room.id)
        except Room.DoesNotExist:
            error_message = "Invalid room ID or password. Please try again."

    return render(request, 'base/join_private_room.html', {'error_message': error_message})


@login_required(login_url='login')
def privateRoomInfo(request):
    return render(request, 'base/private_room_info.html')