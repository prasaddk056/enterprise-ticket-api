from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from tickets.models import Ticket, TicketStatus


User = get_user_model()


class TicketAPIEndpointTests(APITestCase):

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

        self.other_client = User.objects.create_user(
            username="client2",
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

        self.client_ticket = Ticket.objects.create(
            ticket_id="TCK-001",
            issue="Database connection failure",
            category="database",
            client=self.client_user,
        )

        self.other_client_ticket = Ticket.objects.create(
            ticket_id="TCK-002",
            issue="Login failure",
            category="authentication",
            client=self.other_client,
        )

        self.agent_ticket = Ticket.objects.create(
            ticket_id="TCK-003",
            issue="API failure",
            category="backend",
            client=self.client_user,
            assigned_to=self.agent,
            status=TicketStatus.ASSIGNED,
        )

        self.other_agent_ticket = Ticket.objects.create(
            ticket_id="TCK-004",
            issue="Deployment failure",
            category="deployment",
            client=self.client_user,
            assigned_to=self.other_agent,
            status=TicketStatus.ASSIGNED,
        )

    def test_client_sees_only_own_tickets(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.get("/api/tickets/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        ticket_ids = [
            ticket["ticket_id"]
            for ticket in response.data["results"]
        ]

        self.assertIn("TCK-001", ticket_ids)
        self.assertNotIn("TCK-002", ticket_ids)

    def test_support_agent_sees_only_assigned_tickets(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.get("/api/tickets/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        ticket_ids = [
            ticket["ticket_id"]
            for ticket in response.data["results"]
        ]

        self.assertIn("TCK-003", ticket_ids)
        self.assertNotIn("TCK-004", ticket_ids)
        self.assertNotIn("TCK-001", ticket_ids)

    def test_admin_sees_all_tickets(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get("/api/tickets/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        ticket_ids = [
            ticket["ticket_id"]
            for ticket in response.data["results"]
        ]

        self.assertCountEqual(
            ticket_ids,
            [
                "TCK-001",
                "TCK-002",
                "TCK-003",
                "TCK-004",
            ],
        )

    def test_admin_can_assign_ticket(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            f"/api/tickets/{self.client_ticket.id}/assign/",
            {"assigned_to": self.agent.id},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.client_ticket.refresh_from_db()

        self.assertEqual(
            self.client_ticket.assigned_to,
            self.agent,
        )

        self.assertEqual(
            self.client_ticket.status,
            TicketStatus.ASSIGNED,
        )

    def test_assigned_agent_can_update_status(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.patch(
            f"/api/tickets/{self.agent_ticket.id}/status/",
            {"status": TicketStatus.IN_PROGRESS},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.agent_ticket.refresh_from_db()

        self.assertEqual(
            self.agent_ticket.status,
            TicketStatus.IN_PROGRESS,
        )

    def test_wrong_agent_cannot_update_ticket_status(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.patch(
            f"/api/tickets/{self.other_agent_ticket.id}/status/",
            {"status": TicketStatus.IN_PROGRESS},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.other_agent_ticket.refresh_from_db()

        self.assertEqual(
            self.other_agent_ticket.status,
            TicketStatus.ASSIGNED,
        )