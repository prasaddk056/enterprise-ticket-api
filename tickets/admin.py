from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User,Ticket


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Registers the custom User model with Django admin.

    UserAdmin provides the standard Django user management interface
    while allowing us to display and edit our application role.
    """

    fieldsets = UserAdmin.fieldsets + (
        ("Application Role", {"fields": ("role",)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Application Role", {"fields": ("role",)}),
    )

    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """
    Provides ticket management through Django admin.
    """

    list_display = (
        "ticket_id",
        "issue",
        "category",
        "status",
        "is_priority",
        "client",
        "assigned_to",
        "created_at",
    )

    list_filter = (
        "status",
        "category",
        "is_priority",
    )

    search_fields = (
        "ticket_id",
        "issue",
        "client__username",
        "assigned_to__username",
    )