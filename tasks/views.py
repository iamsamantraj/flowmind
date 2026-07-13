from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Task
from .forms import TaskForm
from assistant.gemini_client import ask_gemini


@login_required
def task_list(request):
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    tasks = Task.objects.filter(user=request.user)

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    context = {
        'tasks': tasks,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'pending_count': Task.objects.filter(user=request.user, status='pending').count(),
        'inprogress_count': Task.objects.filter(user=request.user, status='in_progress').count(),
        'completed_count': Task.objects.filter(user=request.user, status='completed').count(),
    }
    return render(request, 'tasks/list.html', context)


@login_required
def task_create(request):
    form = TaskForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        messages.success(request, 'Task created!')
        return redirect('tasks:detail', pk=task.pk)
    return render(request, 'tasks/form.html', {'form': form, 'action': 'Create'})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    return render(request, 'tasks/detail.html', {'task': task})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    form = TaskForm(request.POST or None, instance=task)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Task updated!')
        return redirect('tasks:detail', pk=task.pk)
    return render(request, 'tasks/form.html', {'form': form, 'action': 'Edit', 'task': task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('tasks:list')
    return render(request, 'tasks/confirm_delete.html', {'task': task})


@login_required
@require_POST
def task_toggle_status(request, pk):
    """Quick status toggle from task list"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == 'pending':
        task.status = 'in_progress'
    elif task.status == 'in_progress':
        task.status = 'completed'
    else:
        task.status = 'pending'
    task.save()
    return JsonResponse({'status': task.status})


@login_required
@require_POST
def task_ai_subtasks(request, pk):
    """AI generate subtasks from task title/description"""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    prompt = f"""
    Break down the following task into 5-7 clear, actionable subtasks.
    Each subtask should be specific and completable in one sitting.

    Task: {task.title}
    Description: {task.description or 'No description provided'}

    Return ONLY a JSON array of subtask strings, nothing else.
    Example format: ["Subtask 1", "Subtask 2", "Subtask 3"]
    """

    result = ask_gemini(prompt)

    try:
        # Clean up response and parse JSON
        result = result.strip()
        if result.startswith('```'):
            result = result.split('```')[1]
            if result.startswith('json'):
                result = result[4:]
        subtasks = json.loads(result.strip())
        task.ai_subtasks = subtasks
        task.save()
        return JsonResponse({'subtasks': subtasks})
    except Exception:
        return JsonResponse({'subtasks': [], 'error': 'Could not parse AI response. Try again.'})


@login_required
@require_POST
def task_ai_prioritize(request, pk):
    """AI suggest priority and deadline advice"""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    prompt = f"""
    Analyze this task and give a short prioritization advice in 2-3 sentences.
    Suggest whether the priority level is appropriate and give a tip to complete it efficiently.

    Task: {task.title}
    Current Priority: {task.priority}
    Due Date: {task.due_date or 'Not set'}
    Description: {task.description or 'None'}

    Be direct and actionable.
    """

    advice = ask_gemini(prompt)
    return JsonResponse({'advice': advice})