from rest_framework.permissions import BasePermission

from .models import Role, TicketStatus


class IsAdmin(BasePermission):
    """
    Allows access only to users with the ADMIN role.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class IsSupportAgent(BasePermission):
    """
    Allows access only to users with the SUPPORT_AGENT role.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Role.SUPPORT_AGENT
        )


class IsClient(BasePermission):
    """
    Allows access only to users with the CLIENT role.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == Role.CLIENT
        )


class IsAdminOrSupportAgent(BasePermission):
    """
    Allows access to administrative or support-agent users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            in [Role.ADMIN, Role.SUPPORT_AGENT]
        )

class CanUpdateTicketStatus(BasePermission):
    """
    Allows admins to update any ticket status.

    Support agents can update only tickets assigned to them.
    Clients cannot update ticket status.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                Role.ADMIN,
                Role.SUPPORT_AGENT,
            ]
        )

    def has_object_permission(self, request, view, obj):
        if request.user.role == Role.ADMIN:
            return True

        if request.user.role == Role.SUPPORT_AGENT:
            return obj.assigned_to == request.user

        return False

class CanUpdateTicket(BasePermission):
    """
    Allows admins to update any ticket.

    Support agents can update only tickets assigned to them.
    Clients can update only their own open tickets.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                Role.ADMIN,
                Role.SUPPORT_AGENT,
                Role.CLIENT,
            ]
        )

    def has_object_permission(self, request, view, obj):
        if request.user.role == Role.ADMIN:
            return True

        if request.user.role == Role.SUPPORT_AGENT:
            return obj.assigned_to == request.user

        if request.user.role == Role.CLIENT:
            return (
                obj.client == request.user
                and obj.status == TicketStatus.OPEN
            )

        return False