# Enterprise Ticket Lifecycle Management API

A backend REST API for managing enterprise support tickets with role-based access control, JWT authentication, controlled ticket lifecycle transitions, filtering, search, pagination, automated testing, and Docker support.

## Tech Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- SQLite
- django-filter
- Docker
- Git

## Key Features

- JWT-based authentication
- Role-based access control
- Three application roles:
  - ADMIN
  - SUPPORT_AGENT
  - CLIENT
- Ticket creation and management
- Admin-controlled ticket assignment
- Controlled ticket status transitions
- Role-based ticket visibility
- Ticket update restrictions
- Ticket deletion rules
- Filtering by status, category, and priority
- Search by ticket ID, issue, and category
- Pagination
- Automated API and business-logic tests
- Dockerized application

## Ticket Lifecycle

Tickets follow a controlled lifecycle:

```text
OPEN -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED
```

Direct or invalid status transitions are rejected by the service layer.

For example:

```text
OPEN -> CLOSED
OPEN -> RESOLVED
ASSIGNED -> RESOLVED
CLOSED -> IN_PROGRESS
```

These transitions are rejected because they do not follow the defined lifecycle.

## User Roles

| Role | Responsibilities |
|------|------------------|
| ADMIN | View all tickets, assign tickets, update ticket status, update tickets, delete tickets |
| SUPPORT_AGENT | View assigned tickets, update assigned tickets, update status of assigned tickets |
| CLIENT | Create tickets, view own tickets, update own open tickets, delete own open tickets |

## Project Structure

```text
enterprise-ticket-api/
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tickets/
│   ├── migrations/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_auth.py
│   │   ├── test_lifecycle.py
│   │   ├── test_permissions.py
│   │   └── test_tickets.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── services.py
│   ├── urls.py
│   └── views.py
├── .dockerignore
├── .gitignore
├── Dockerfile
├── manage.py
├── README.md
└── requirements.txt
```

## Installation

### Clone the repository

```bash
git clone https://github.com/prasaddk056/enterprise-ticket-api.git
cd enterprise-ticket-api
```

### Create and activate virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Apply migrations

```bash
python manage.py migrate
```

### Create an admin user

```bash
python manage.py createsuperuser
```

Follow the prompts to create the Django admin account.

### Start the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

Django Admin:

```text
http://127.0.0.1:8000/admin/
```

## Run with Docker

Make sure Docker Desktop is running.

### Build the Docker image

```bash
docker build -t enterprise-ticket-api .
```

### Run the container

```bash
docker run --rm -p 8000:8000 enterprise-ticket-api
```

The API will be available at:

```text
http://localhost:8000/api/
```

For example:

```text
http://localhost:8000/api/tickets/
```

To stop the container, press:

```text
Ctrl+C
```

## Authentication

The API uses JWT authentication.

### Login

```http
POST /api/auth/login/
```

Example request:

```json
{
    "username": "client1",
    "password": "your-password"
}
```

Successful login returns:

```json
{
    "refresh": "refresh-token",
    "access": "access-token",
    "user": {
        "id": 2,
        "username": "client1",
        "email": "client1@example.com",
        "role": "CLIENT"
    }
}
```

Use the access token in subsequent requests:

```http
Authorization: Bearer <access-token>
```

### Refresh token

```http
POST /api/auth/refresh/
```

Example request:

```json
{
    "refresh": "<refresh-token>"
}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | Obtain JWT access and refresh tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET | `/api/tickets/` | List tickets based on user role |
| POST | `/api/tickets/create/` | Create a new ticket |
| POST | `/api/tickets/<id>/assign/` | Assign ticket to support agent |
| PATCH | `/api/tickets/<id>/status/` | Update ticket status |
| PATCH | `/api/tickets/<id>/update/` | Update editable ticket fields |
| DELETE | `/api/tickets/<id>/` | Delete a ticket based on role and status |

## Ticket Creation

Only authenticated clients can create tickets.

```http
POST /api/tickets/create/
```

Example:

```json
{
    "ticket_id": "TCK-001",
    "issue": "Database connection failure",
    "category": "database",
    "is_priority": true,
    "comment": "Application is unable to connect to DB."
}
```

The authenticated user is automatically assigned as the ticket client.

New tickets start with:

```text
OPEN
```

The client cannot directly set protected fields such as:

- status
- client
- assigned_to
- timestamps
- resolved_at

## Ticket Assignment

Only administrators can assign tickets.

```http
POST /api/tickets/<id>/assign/
```

Example:

```json
{
    "assigned_to": 3
}
```

The selected user must have the `SUPPORT_AGENT` role.

A successfully assigned ticket changes from:

```text
OPEN -> ASSIGNED
```

Tickets that are not in the `OPEN` state cannot be assigned.

## Ticket Status Updates

Status changes are handled through a dedicated endpoint:

```http
PATCH /api/tickets/<id>/status/
```

Example:

```json
{
    "status": "IN_PROGRESS"
}
```

Valid transitions are:

```text
OPEN -> ASSIGNED
ASSIGNED -> IN_PROGRESS
IN_PROGRESS -> RESOLVED
RESOLVED -> CLOSED
```

Admins can update the status of any ticket.

Support agents can update the status only for tickets assigned to them.

Clients cannot update ticket status.

When a ticket moves to `RESOLVED`, the `resolved_at` timestamp is automatically recorded.

## Ticket Updates

Editable ticket information can be updated through:

```http
PATCH /api/tickets/<id>/update/
```

Example:

```json
{
    "issue": "Updated database connection failure",
    "category": "database",
    "is_priority": false,
    "comment": "Additional troubleshooting information."
}
```

The following fields cannot be modified through this endpoint:

- status
- client
- assigned_to
- created_at
- updated_at
- resolved_at

Status changes must use the dedicated status endpoint.

## Ticket Visibility

Ticket visibility is restricted by role.

### ADMIN

Administrators can view all tickets.

### SUPPORT_AGENT

Support agents can view only tickets assigned to them.

### CLIENT

Clients can view only tickets they created.

These restrictions are applied at the queryset level before filtering and searching.

## Ticket Deletion

Deletion rules are enforced by the service layer.

### ADMIN

Administrators can delete any ticket.

### CLIENT

Clients can delete only their own tickets while the ticket is still:

```text
OPEN
```

### SUPPORT_AGENT

Support agents cannot delete tickets.

## Filtering

Ticket lists support filtering by:

- status
- category
- priority

Examples:

```http
GET /api/tickets/?status=OPEN
```

```http
GET /api/tickets/?category=database
```

```http
GET /api/tickets/?is_priority=true
```

Filters can also be combined:

```http
GET /api/tickets/?status=OPEN&category=database
```

## Search

Search is supported using the `search` query parameter.

Search fields:

- ticket ID
- issue
- category

Example:

```http
GET /api/tickets/?search=database
```

Search can be combined with filtering and pagination:

```http
GET /api/tickets/?search=database&status=OPEN&page=2
```

Search and filtering are applied within the tickets visible to the authenticated user's role.

## Pagination

Ticket listing uses Django REST Framework pagination.

The default page size is:

```text
10 tickets per page
```

Example:

```http
GET /api/tickets/?page=2
```

A paginated response contains:

```json
{
    "count": 25,
    "next": "...",
    "previous": null,
    "results": []
}
```

## Testing

The project includes automated tests covering:

- JWT authentication
- Ticket creation
- Authentication requirements
- Role-based permissions
- Ticket visibility
- Ticket assignment
- Status updates
- Invalid lifecycle transitions
- Ticket update restrictions
- API endpoint behavior

Run the complete test suite with:

```bash
python manage.py test
```

## Development Notes

The project separates responsibilities across different layers:

```text
Models
  ↓
Serializers
  ↓
Views
  ↓
Permissions
  ↓
Services
```

Business rules such as ticket assignment, lifecycle transitions, and deletion restrictions are handled in the service layer rather than being implemented entirely inside API views.

Role-based queryset filtering is applied at the API level to prevent users from accessing tickets outside their permitted scope.

## Future Improvements

Potential future enhancements include:

- PostgreSQL database
- OpenAPI / Swagger documentation
- CI/CD pipeline
- Structured application logging
- Email or notification integration
- Production deployment configuration

## License

This project is a portfolio and learning project created to demonstrate backend development, REST API design, authentication, authorization, business logic, testing, and containerization.