from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Workspace


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'username', 'is_staff', 'created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('avatar', 'bio')}),
    )


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']