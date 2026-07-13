from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from notes.models import Note
from tasks.models import Task
from goals.models import Goal
from assistant.gemini_client import ask_gemini
from .serializers import (
    NoteSerializer, TaskSerializer,
    GoalSerializer, UserSerializer
)
import json


# ── Permission: owner only ──
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


# ── Dashboard Stats ──
class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'total_notes': Note.objects.filter(user=user).count(),
            'total_tasks': Task.objects.filter(user=user).count(),
            'completed_tasks': Task.objects.filter(user=user, status='completed').count(),
            'pending_tasks': Task.objects.filter(user=user, status='pending').count(),
            'inprogress_tasks': Task.objects.filter(user=user, status='in_progress').count(),
            'total_goals': Goal.objects.filter(user=user).count(),
            'active_goals': Goal.objects.filter(user=user, status='active').count(),
        }
        return Response(data)


# ── Notes API ──
class NoteListCreateView(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Note.objects.filter(user=self.request.user)
        q = self.request.query_params.get('q', '')
        if q:
            queryset = queryset.filter(title__icontains=q) | queryset.filter(content__icontains=q)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user)


class NoteAISummarizeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        note = get_object_or_404(Note, pk=pk, user=request.user)
        if not note.content.strip():
            return Response({'error': 'Note content is empty.'}, status=400)

        prompt = f"""Summarize this note in 3-5 bullet points. Be concise.
Title: {note.title}
Content: {note.content}
Return only bullet points."""

        summary = ask_gemini(prompt)
        note.ai_summary = summary
        note.save()
        return Response({'summary': summary})


# ── Tasks API ──
class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)
        status = self.request.query_params.get('status', '')
        priority = self.request.query_params.get('priority', '')
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class TaskAISubtasksView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        prompt = f"""Break this task into 5-7 actionable subtasks.
Task: {task.title}
Description: {task.description or 'None'}
Return ONLY a JSON array of strings."""

        result = ask_gemini(prompt)
        try:
            result = result.strip()
            if result.startswith('```'):
                result = result.split('```')[1]
                if result.startswith('json'):
                    result = result[4:]
            subtasks = json.loads(result.strip())
            task.ai_subtasks = subtasks
            task.save()
            return Response({'subtasks': subtasks})
        except Exception:
            return Response({'error': 'Could not parse AI response'}, status=400)


# ── Goals API ──
class GoalListCreateView(generics.ListCreateAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Goal.objects.filter(user=self.request.user)
        status = self.request.query_params.get('status', '')
        category = self.request.query_params.get('category', '')
        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)


class GoalAIAdviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        goal = get_object_or_404(Goal, pk=pk, user=request.user)
        prompt = f"""Give 3-4 sentences of actionable coaching advice for this goal.
Goal: {goal.title}
Category: {goal.category}
Progress: {goal.progress}%
Target: {goal.target_date or 'Not set'}"""

        advice = ask_gemini(prompt)
        goal.ai_advice = advice
        goal.save()
        return Response({'advice': advice})


# ── User Profile API ──
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)