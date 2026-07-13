from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Goal
from .forms import GoalForm
from assistant.gemini_client import ask_gemini


@login_required
def goal_list(request):
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    goals = Goal.objects.filter(user=request.user)

    if category_filter:
        goals = goals.filter(category=category_filter)
    if status_filter:
        goals = goals.filter(status=status_filter)

    context = {
        'goals': goals,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'active_count': Goal.objects.filter(user=request.user, status='active').count(),
        'completed_count': Goal.objects.filter(user=request.user, status='completed').count(),
        'paused_count': Goal.objects.filter(user=request.user, status='paused').count(),
    }
    return render(request, 'goals/list.html', context)


@login_required
def goal_create(request):
    form = GoalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        messages.success(request, 'Goal created!')
        return redirect('goals:detail', pk=goal.pk)
    return render(request, 'goals/form.html', {'form': form, 'action': 'Create'})


@login_required
def goal_detail(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    return render(request, 'goals/detail.html', {'goal': goal})


@login_required
def goal_edit(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    form = GoalForm(request.POST or None, instance=goal)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Goal updated!')
        return redirect('goals:detail', pk=goal.pk)
    return render(request, 'goals/form.html', {'form': form, 'action': 'Edit', 'goal': goal})


@login_required
def goal_delete(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted.')
        return redirect('goals:list')
    return render(request, 'goals/confirm_delete.html', {'goal': goal})


@login_required
@require_POST
def goal_update_progress(request, pk):
    """Update progress via AJAX slider"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    data = json.loads(request.body)
    progress = int(data.get('progress', 0))
    progress = max(0, min(100, progress))
    goal.progress = progress
    if progress == 100:
        goal.status = 'completed'
    goal.save()
    return JsonResponse({'progress': goal.progress, 'status': goal.status})


@login_required
@require_POST
def goal_ai_coaching(request, pk):
    """AI coaching advice for this goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    prompt = f"""
    Act as a professional life coach. Give motivating, practical advice 
    for someone working toward this goal.

    Goal: {goal.title}
    Category: {goal.category}
    Description: {goal.description or 'Not provided'}
    Current Progress: {goal.progress}%
    Target Date: {goal.target_date or 'Not set'}
    Status: {goal.status}

    Give 3-4 specific, actionable tips to help them achieve this goal faster.
    Be encouraging but realistic. Keep it concise.
    """

    advice = ask_gemini(prompt)
    goal.ai_advice = advice
    goal.save()
    return JsonResponse({'advice': advice})


@login_required
@require_POST
def goal_ai_milestones(request, pk):
    """AI generate milestone roadmap for goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)

    prompt = f"""
    Create a milestone roadmap for this goal. Break it into 5 clear milestones
    that mark meaningful progress points from start to completion.

    Goal: {goal.title}
    Description: {goal.description or 'Not provided'}
    Target Date: {goal.target_date or 'Not set'}

    Return ONLY a JSON array of milestone objects with this exact format:
    [{{"milestone": "Milestone title", "description": "What to do", "percent": 20}}, ...]
    The percent values should be 20, 40, 60, 80, 100.
    No extra text, just the JSON array.
    """

    result = ask_gemini(prompt)

    try:
        result = result.strip()
        if result.startswith('```'):
            result = result.split('```')[1]
            if result.startswith('json'):
                result = result[4:]
        milestones = json.loads(result.strip())
        goal.ai_milestones = milestones
        goal.save()
        return JsonResponse({'milestones': milestones})
    except Exception:
        return JsonResponse({'milestones': [], 'error': 'Could not parse milestones. Try again.'})