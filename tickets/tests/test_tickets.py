from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Ticket


User = get_user_model()


class TicketCreationTests(APITestCase):
    """
    Tests ticket creation behavior.
    """

    def setUp(self):
        self.client_user = User.objects.create_user(
            username="client1",
            password="testpass123",
            role="CLIENT",
        )

    def test_authenticated_client_can_create_ticket(self):
        self.client.force_authenticate(
            user=self.client_user
        )

        response = self.client.post(
            "/api/tickets/create/",
            {
                "ticket_id": "TCK-001",
                "issue": "Database connection failure",
                "category": "database",
                "is_priority": True,
                "comment": "Application is unable to connect to DB.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Ticket.objects.count(),
            1,
        )

        ticket = Ticket.objects.first()

        self.assertEqual(
            ticket.client,
            self.client_user,
        )

        self.assertEqual(
            ticket.status,
            "OPEN",
        )

    def test_unauthenticated_user_cannot_create_ticket(self):
        response = self.client.post(
            "/api/tickets/create/",
            {
                "ticket_id": "TCK-002",
                "issue": "Database connection failure",
                "category": "database",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertEqual(
            Ticket.objects.count(),
            0,
        )