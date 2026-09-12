from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    TicketCreateView,
    TicketListView,
    TicketAssignView,
    TicketStatusUpdateView,
    TicketDeleteView,
    TicketUpdateView,
    TicketActivityListView,
)


urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("tickets/", TicketListView.as_view(), name="ticket_list"),
    path("tickets/create/", TicketCreateView.as_view(), name="ticket_create"),
    path("tickets/<int:pk>/assign/",TicketAssignView.as_view(),name="ticket_assign",),
    path( "tickets/<int:pk>/status/",TicketStatusUpdateView.as_view(),name="ticket_status_update",),
    path("tickets/<int:pk>/update/",TicketUpdateView.as_view(),name="ticket_update",),
    path("tickets/<int:pk>/activities/",TicketActivityListView.as_view(),name="ticket_activities",),
    path("tickets/<int:pk>/",TicketDeleteView.as_view(),name="ticket_delete",),

]