from rest_framework import serializers
from notes.models import Note, Tag
from tasks.models import Task
from goals.models import Goal
from accounts.models import CustomUser


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class NoteSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Note
        fields = [
            'id', 'title', 'content', 'ai_summary',
            'tags', 'is_pinned', 'created_at', 'updated_at'
        ]
        read_only_fields = ['ai_summary', 'created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status',
            'priority', 'due_date', 'ai_subtasks', 'created_at'
        ]
        read_only_fields = ['ai_subtasks', 'created_at']


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = [
            'id', 'title', 'description', 'category',
            'status', 'progress', 'target_date',
            'ai_advice', 'ai_milestones', 'created_at'
        ]
        read_only_fields = ['ai_advice', 'ai_milestones', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'bio', 'avatar', 'created_at']
        read_only_fields = ['created_at']