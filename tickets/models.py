from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    SUPPORT_AGENT = "SUPPORT_AGENT", "Support Agent"
    CLIENT = "CLIENT", "Client"


class User(AbstractUser):
    """
    Custom user model for the ticket management system.

    Each user has an application role that determines
    which actions they are authorized to perform.
    """

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class TicketStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    ASSIGNED = "ASSIGNED", "Assigned"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    RESOLVED = "RESOLVED", "Resolved"
    CLOSED = "CLOSED", "Closed"


class Ticket(models.Model):
    """
    Represents a support ticket created by a client.

    A ticket moves through a controlled lifecycle:

    OPEN -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED
    """

    ticket_id = models.CharField(
        max_length=50,
        unique=True,
    )

    issue = models.CharField(
        max_length=255,
    )

    category = models.CharField(
        max_length=50,
    )

    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN,
    )

    is_priority = models.BooleanField(
        default=False,
    )

    comment = models.TextField(
        blank=True,
    )

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_tickets",
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.ticket_id} - {self.status}"

class TicketActivity(models.Model):
    """
    Stores an audit trail of important actions performed on a ticket.
    """

    ticket = models.ForeignKey(
    Ticket,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="activities",
    )
    
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ticket_activities",
    )
    action = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticket.ticket_id} - {self.action}"