from django.core.exceptions import ValidationError

from .models import Role, Ticket, TicketStatus, User


def assign_ticket(ticket: Ticket, support_agent: User) -> Ticket:
    """
    Assigns an open ticket to a support agent.

    Assignment is a business operation, so the lifecycle rule
    is enforced here rather than inside the API view.
    """

    if ticket.status != TicketStatus.OPEN:
        raise ValidationError(
            "Only open tickets can be assigned."
        )

    if support_agent.role != Role.SUPPORT_AGENT:
        raise ValidationError(
            "Ticket can only be assigned to a support agent."
        )

    ticket.assigned_to = support_agent
    ticket.status = TicketStatus.ASSIGNED
    ticket.save(
        update_fields=[
            "assigned_to",
            "status",
            "updated_at",
        ]
    )

    return ticket

def update_ticket_status(ticket: Ticket, new_status: str) -> Ticket:
    """
    Updates a ticket status only when the requested transition
    follows the defined ticket lifecycle.
    """

    valid_transitions = {
        TicketStatus.OPEN: [
            TicketStatus.ASSIGNED,
        ],
        TicketStatus.ASSIGNED: [
            TicketStatus.IN_PROGRESS,
        ],
        TicketStatus.IN_PROGRESS: [
            TicketStatus.RESOLVED,
        ],
        TicketStatus.RESOLVED: [
            TicketStatus.CLOSED,
        ],
        TicketStatus.CLOSED: [],
    }

    allowed_statuses = valid_transitions.get(ticket.status, [])

    if new_status not in allowed_statuses:
        raise ValidationError(
            f"Invalid status transition: "
            f"{ticket.status} -> {new_status}"
        )

    ticket.status = new_status

    if new_status == TicketStatus.RESOLVED:
        from django.utils import timezone

        ticket.resolved_at = timezone.now()

    ticket.save(
        update_fields=[
            "status",
            "resolved_at",
            "updated_at",
        ]
    )

    return ticket

def delete_ticket(ticket: Ticket, user: User) -> None:
    """
    Deletes a ticket only when the user is authorized and
    the ticket is still eligible for deletion.
    """

    if user.role == Role.ADMIN:
        ticket.delete()
        return

    if user.role == Role.CLIENT:
        if ticket.client != user:
            raise ValidationError(
                "You can only delete your own tickets."
            )

        if ticket.status != TicketStatus.OPEN:
            raise ValidationError(
                "Only open tickets can be deleted."
            )

        ticket.delete()
        return

    raise ValidationError(
        "You do not have permission to delete tickets."
    )