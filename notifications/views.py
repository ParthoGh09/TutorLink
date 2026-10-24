from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import Notification, NotificationType


def get_default_user():
    user, _ = User.objects.get_or_create(
        username='ayesha_rahman',
        defaults={'first_name': 'Ayesha', 'last_name': 'Rahman', 'email': 'ayesha.rahman@gmail.com'}
    )
    return user


def notification_list_view(request):
    user = request.user if request.user.is_authenticated else get_default_user()
    
    selected_filter = request.GET.get('filter', 'ALL').upper()
    
    notifications = Notification.objects.filter(recipient=user)
    
    if selected_filter != 'ALL':
        notifications = notifications.filter(notification_type=selected_filter)
        
    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
    
    one_week_ago = timezone.now() - timedelta(days=7)
    this_week_count = Notification.objects.filter(recipient=user, created_at__gte=one_week_ago).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'this_week_count': this_week_count,
        'selected_filter': selected_filter,
        'filter_types': NotificationType.choices,
        'current_user': user,
    }
    return render(request, 'notifications/notification_list.html', context)


def mark_as_read_view(request, notification_id):
    user = request.user if request.user.is_authenticated else get_default_user()
    notification = get_object_or_404(Notification, id=notification_id, recipient=user)
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'is_read': True})
    
    messages.success(request, f"Marked '{notification.title}' as read.")
    return redirect('notifications:notification_list')


def mark_all_as_read_view(request):
    user = request.user if request.user.is_authenticated else get_default_user()
    Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
        
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications:notification_list')
