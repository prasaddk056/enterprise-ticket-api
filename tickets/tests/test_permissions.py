from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Ticket


User = get_user_model()


class TicketPermissionTests(APITestCase):
    """
    Tests role-based access control for ticket operations.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            password="testpass123",
            role="ADMIN",
        )

        self.client_user = User.objects.create_user(
            username="client1",
            password="testpass123",
            role="CLIENT",
        )

        self.agent = User.objects.create_user(
            username="agent1",
            password="testpass123",
            role="SUPPORT_AGENT",
        )

        self.other_agent = User.objects.create_user(
            username="agent2",
            password="testpass123",
            role="SUPPORT_AGENT",
        )

        self.ticket = Ticket.objects.create(
            ticket_id="TCK-001",
            issue="Database connection failure",
            category="database",
            client=self.client_user,
        )

    def test_client_cannot_assign_ticket(self):
        self.client.force_authenticate(
            user=self.client_user
        )

        response = self.client.post(
            f"/api/tickets/{self.ticket.id}/assign/",
            {
                "assigned_to": self.agent.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_support_agent_cannot_assign_ticket(self):
        self.client.force_authenticate(
            user=self.agent
        )

        response = self.client.post(
            f"/api/tickets/{self.ticket.id}/assign/",
            {
                "assigned_to": self.other_agent.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_assign_ticket(self):
        self.client.force_authenticate(
            user=self.admin
        )

        response = self.client.post(
            f"/api/tickets/{self.ticket.id}/assign/",
            {
                "assigned_to": self.agent.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.assigned_to,
            self.agent,
        )

        self.assertEqual(
            self.ticket.status,
            "ASSIGNED",
        )

    def test_client_cannot_update_ticket_status(self):
        self.client.force_authenticate(
            user=self.client_user
        )

        response = self.client.patch(
            f"/api/tickets/{self.ticket.id}/status/",
            {
                "status": "ASSIGNED",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unassigned_agent_cannot_update_ticket_status(self):
        self.ticket.assigned_to = self.agent
        self.ticket.status = "ASSIGNED"
        self.ticket.save()

        self.client.force_authenticate(
            user=self.other_agent
        )

        response = self.client.patch(
            f"/api/tickets/{self.ticket.id}/status/",
            {
                "status": "IN_PROGRESS",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )