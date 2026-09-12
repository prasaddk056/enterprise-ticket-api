from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role,Ticket,TicketStatus,TicketActivity
from django.contrib.auth import get_user_model

class LoginSerializer(TokenObtainPairSerializer):
    """
    Generates JWT access and refresh tokens for authenticated users.
    """

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
        }

        return data


class TicketSerializer(serializers.ModelSerializer):
    """
    Serializer responsible for converting Ticket objects
    to/from JSON and validating incoming ticket data.
    """

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticket_id",
            "issue",
            "category",
            "status",
            "is_priority",
            "comment",
            "client",
            "assigned_to",
            "created_at",
            "updated_at",
            "resolved_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "client",
            "assigned_to",
            "created_at",
            "updated_at",
            "resolved_at",
        ]

    def validate_issue(self, value):
        """
        Prevent tickets from being created with an empty issue.
        """

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Issue description cannot be empty."
            )

        return value

    def validate_category(self, value):
        """
        Normalize category input to avoid inconsistent values.
        """

        value = value.strip().lower()

        if not value:
            raise serializers.ValidationError(
                "Category cannot be empty."
            )

        return value

class AssignTicketSerializer(serializers.Serializer):
    """
    Validates the support agent selected for ticket assignment.
    """

    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(
        role=Role.SUPPORT_AGENT
        )
    )

class UpdateTicketStatusSerializer(serializers.Serializer):
    """
    Validates the new status requested for a ticket.
    """

    status = serializers.ChoiceField(
        choices=TicketStatus.choices
    )

class TicketUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating editable ticket information.

    Protected fields such as status, client, assignment,
    and timestamps cannot be modified directly.
    """

    class Meta:
        model = Ticket
        fields = [
            "issue",
            "category",
            "is_priority",
            "comment",
        ]

    def validate_issue(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Issue description cannot be empty."
            )

        return value

    def validate_category(self, value):
        value = value.strip().lower()

        if not value:
            raise serializers.ValidationError(
                "Category cannot be empty."
            )

        return value

class TicketActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for displaying the audit history of a ticket.
    """

    performed_by = serializers.CharField(
        source="performed_by.username",
        read_only=True,
    )

    class Meta:
        model = TicketActivity
        fields = [
            "id",
            "ticket",
            "performed_by",
            "action",
            "description",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "performed_by",
            "action",
            "description",
            "created_at",
        ]