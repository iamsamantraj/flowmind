from django.db import models
from django.conf import settings


class Goal(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]
    CATEGORY_CHOICES = [
        ('personal', 'Personal'),
        ('career', 'Career'),
        ('health', 'Health'),
        ('finance', 'Finance'),
        ('learning', 'Learning'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='personal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    progress = models.IntegerField(default=0)  # 0-100
    target_date = models.DateField(null=True, blank=True)
    ai_advice = models.TextField(blank=True)
    ai_milestones = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title