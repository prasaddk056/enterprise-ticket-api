from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from tickets.models import Ticket, TicketStatus
from tickets.services import update_ticket_status


User = get_user_model()


class TicketLifecycleTests(TestCase):
    """
    Tests valid and invalid ticket status transitions.
    """

    def setUp(self):
        self.client_user = User.objects.create_user(
            username="client1",
            password="testpass123",
            role="CLIENT",
        )

        self.ticket = Ticket.objects.create(
            ticket_id="TCK-001",
            issue="Database connection failure",
            category="database",
            client=self.client_user,
        )

    def test_valid_status_transitions(self):
        update_ticket_status(
            self.ticket,
            TicketStatus.ASSIGNED,
        )

        self.assertEqual(
            self.ticket.status,
            TicketStatus.ASSIGNED,
        )

        update_ticket_status(
            self.ticket,
            TicketStatus.IN_PROGRESS,
        )

        self.assertEqual(
            self.ticket.status,
            TicketStatus.IN_PROGRESS,
        )

        update_ticket_status(
            self.ticket,
            TicketStatus.RESOLVED,
        )

        self.assertEqual(
            self.ticket.status,
            TicketStatus.RESOLVED,
        )

        self.assertIsNotNone(
            self.ticket.resolved_at
        )

        update_ticket_status(
            self.ticket,
            TicketStatus.CLOSED,
        )

        self.assertEqual(
            self.ticket.status,
            TicketStatus.CLOSED,
        )

    def test_open_ticket_cannot_be_closed_directly(self):
        with self.assertRaises(ValidationError):
            update_ticket_status(
                self.ticket,
                TicketStatus.CLOSED,
            )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.status,
            TicketStatus.OPEN,
        )

    def test_open_ticket_cannot_be_resolved_directly(self):
        with self.assertRaises(ValidationError):
            update_ticket_status(
                self.ticket,
                TicketStatus.RESOLVED,
            )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.status,
            TicketStatus.OPEN,
        )

    def test_closed_ticket_cannot_move_back_to_in_progress(self):
        self.ticket.status = TicketStatus.CLOSED
        self.ticket.save()

        with self.assertRaises(ValidationError):
            update_ticket_status(
                self.ticket,
                TicketStatus.IN_PROGRESS,
            )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.status,
            TicketStatus.CLOSED,
        )