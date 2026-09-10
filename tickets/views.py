from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from .models import Role, Ticket, TicketStatus
from .permissions import (
    CanUpdateTicket,
    CanUpdateTicketStatus,
    IsAdmin,
    IsClient,
)

from .serializers import (
    AssignTicketSerializer,
    LoginSerializer,
    TicketSerializer,
    TicketUpdateSerializer,
    UpdateTicketStatusSerializer,
)

from .services import (
    assign_ticket,
    update_ticket_status,
    delete_ticket,
)


class LoginView(TokenObtainPairView):
    """
    Authenticates a user and returns access and refresh JWT tokens.
    """

    serializer_class = LoginSerializer

class TicketCreateView(generics.CreateAPIView):
    """
    Allows authenticated clients to create support tickets.

    The client is taken from the authenticated JWT user rather than
    accepting a client ID from the request body.
    """

    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated, IsClient]

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


class TicketListView(generics.ListAPIView):
    """
    Returns tickets based on the authenticated user's role.

    Clients see their own tickets.
    Support agents see tickets assigned to them.
    Admins see all tickets.
    """

    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    filterset_fields = [
    "status",
    "category",
    "is_priority",
    ]

    search_fields = [
    "ticket_id",
    "issue",
    "category",
    ]

    def get_queryset(self):
        user = self.request.user

        if user.role == Role.ADMIN:
            queryset = Ticket.objects.all()
        elif user.role == Role.SUPPORT_AGENT:
            queryset = Ticket.objects.filter(assigned_to=user)
        else:
            queryset = Ticket.objects.filter(client=user)

        return queryset.order_by("-created_at")
    

class TicketAssignView(generics.GenericAPIView):
    """
    Allows an admin to assign an open ticket to a support agent.
    """

    serializer_class = AssignTicketSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            assign_ticket(
                ticket=ticket,
                support_agent=serializer.validated_data["assigned_to"],
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )

class TicketStatusUpdateView(generics.GenericAPIView):
    """
    Allows authorized users to move a ticket through its
    defined lifecycle.
    """

    serializer_class = UpdateTicketStatusSerializer
    permission_classes = [CanUpdateTicketStatus]

    def patch(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        self.check_object_permissions(request, ticket)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            update_ticket_status(
                ticket=ticket,
                new_status=serializer.validated_data["status"],
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )

class TicketDeleteView(generics.GenericAPIView):
    """
    Deletes a ticket according to the application's
    deletion policy.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        try:
            delete_ticket(
                ticket=ticket,
                user=request.user,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

class TicketUpdateView(generics.GenericAPIView):
    """
    Updates editable ticket information for an authorized user.
    """

    serializer_class = TicketUpdateSerializer
    permission_classes = [CanUpdateTicket]

    def patch(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)

        self.check_object_permissions(request, ticket)

        serializer = self.get_serializer(
            ticket,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )