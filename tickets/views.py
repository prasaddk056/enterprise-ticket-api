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
    TicketActivitySerializer,
)

from .services import (
    assign_ticket,
    update_ticket_status,
    delete_ticket,
    create_ticket_activity
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
        ticket = serializer.save(client=self.request.user)

        create_ticket_activity(
            ticket=ticket,
            performed_by=self.request.user,
            action="CREATED",
            description="Ticket created",
        )


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

        support_agent = serializer.validated_data["assigned_to"]

        try:
            assign_ticket(
                ticket=ticket,
                support_agent=support_agent,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        create_ticket_activity(
            ticket=ticket,
            performed_by=request.user,
            action="ASSIGNED",
            description=f"Ticket assigned to {support_agent.username}",
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

        old_status = ticket.status

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]

        try:
            update_ticket_status(
                ticket=ticket,
                new_status=new_status,
            )
        except ValidationError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        create_ticket_activity(
            ticket=ticket,
            performed_by=request.user,
            action="STATUS_CHANGED",
            description=(
                f"Status changed from {old_status} to {new_status}"
            ),
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

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )    

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

        updated_fields = ", ".join(serializer.validated_data.keys())

        create_ticket_activity(
            ticket=ticket,
            performed_by=request.user,
            action="UPDATED",
            description=f"Updated fields: {updated_fields}",
        )

        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )

class TicketActivityListView(generics.ListAPIView):
    """
    Returns the audit history of a ticket.

    Users can only view activities for tickets they are
    authorized to see.
    """

    serializer_class = TicketActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        ticket = get_object_or_404(
            Ticket,
            pk=self.kwargs["pk"],
        )

        user = self.request.user

        if user.role == Role.ADMIN:
            return ticket.activities.all()

        if user.role == Role.SUPPORT_AGENT:
            if ticket.assigned_to == user:
                return ticket.activities.all()

        if user.role == Role.CLIENT:
            if ticket.client == user:
                return ticket.activities.all()

        return ticket.activities.none()