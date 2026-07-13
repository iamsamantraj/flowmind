from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import Workspace


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        Workspace.objects.create(owner=user, name=f"{user.username}'s Workspace")
        login(request, user)
        messages.success(request, 'Account created! Welcome to FlowMind 🚀')
        return redirect('dashboard:home')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard:home')
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    user = request.user
    workspace = getattr(user, 'workspace', None)

    # Stats for profile
    from notes.models import Note
    from tasks.models import Task
    from goals.models import Goal

    stats = {
        'total_notes': Note.objects.filter(user=user).count(),
        'total_tasks': Task.objects.filter(user=user).count(),
        'completed_tasks': Task.objects.filter(user=user, status='completed').count(),
        'total_goals': Goal.objects.filter(user=user).count(),
        'active_goals': Goal.objects.filter(user=user, status='active').count(),
        'completed_goals': Goal.objects.filter(user=user, status='completed').count(),
    }

    # Handle profile update
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        bio = request.POST.get('bio', '').strip()
        avatar = request.FILES.get('avatar')

        if username and username != user.username:
            from accounts.models import CustomUser
            if CustomUser.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, 'Username already taken.')
                return redirect('accounts:profile')
            user.username = username

        if bio is not None:
            user.bio = bio

        if avatar:
            user.avatar = avatar

        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'user': user,
        'workspace': workspace,
        'stats': stats,
    })