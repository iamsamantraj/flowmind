from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone
from notes.models import Note
from tasks.models import Task
from goals.models import Goal
import datetime
import json


@login_required
def home(request):
    user = request.user
    today = timezone.now().date()

    # Stats
    total_notes = Note.objects.filter(user=user).count()
    total_tasks = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, status='completed').count()
    pending_tasks = Task.objects.filter(user=user, status='pending').count()
    inprogress_tasks = Task.objects.filter(user=user, status='in_progress').count()
    total_goals = Goal.objects.filter(user=user).count()
    active_goals = Goal.objects.filter(user=user, status='active').count()
    completed_goals = Goal.objects.filter(user=user, status='completed').count()

    # Completion rate
    completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)

    # Average goal progress
    goals = Goal.objects.filter(user=user)
    avg_progress = round(sum(g.progress for g in goals) / goals.count()) if goals.count() > 0 else 0

    # Recent items
    recent_notes = Note.objects.filter(user=user).order_by('-created_at')[:4]
    upcoming_tasks = Task.objects.filter(
        user=user, status__in=['pending', 'in_progress']
    ).order_by('due_date')[:5]
    active_goal_list = Goal.objects.filter(user=user, status='active').order_by('target_date')[:4]

    # Chart data — tasks by status
    task_status_data = {
        'labels': ['Pending', 'In Progress', 'Completed'],
        'data': [pending_tasks, inprogress_tasks, completed_tasks],
        'colors': ['#fbbf24', '#60a5fa', '#4ade80']
    }

    # Chart data — goals by category
    goal_categories = Goal.objects.filter(user=user).values('category').annotate(count=Count('id'))
    goal_category_data = {
        'labels': [g['category'].capitalize() for g in goal_categories],
        'data': [g['count'] for g in goal_categories],
        'colors': ['#c084fc', '#60a5fa', '#4ade80', '#fbbf24', '#f87171', '#888']
    }

    # Chart data — notes created last 7 days
    notes_last_7 = []
    labels_7 = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        count = Note.objects.filter(user=user, created_at__date=day).count()
        notes_last_7.append(count)
        labels_7.append(day.strftime('%a'))

    notes_chart_data = {
        'labels': labels_7,
        'data': notes_last_7,
    }

    context = {
        'total_notes': total_notes,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'total_goals': total_goals,
        'active_goals': active_goals,
        'completed_goals': completed_goals,
        'completion_rate': completion_rate,
        'avg_progress': avg_progress,
        'recent_notes': recent_notes,
        'upcoming_tasks': upcoming_tasks,
        'active_goal_list': active_goal_list,
        'task_status_data': json.dumps(task_status_data),
        'goal_category_data': json.dumps(goal_category_data),
        'notes_chart_data': json.dumps(notes_chart_data),
    }
    return render(request, 'dashboard/home.html', context)