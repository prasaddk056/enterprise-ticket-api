# Enterprise Ticket Lifecycle Management API

A role-based ticket management REST API built with Django REST Framework.

The application simulates an enterprise support workflow where clients create tickets, administrators assign tickets to support agents, and agents manage tickets through a controlled ticket lifecycle.

## Tech Stack

* Python
* Django
* Django REST Framework
* JWT Authentication
* SQLite
* django-filter
* Git

## Key Features

* JWT-based authentication
* Role-based access control
* Client ticket creation
* Admin ticket assignment
* Controlled ticket lifecycle
* Role-based ticket visibility
* Ticket update and deletion rules
* Filtering and search
* Pagination
* Automated API and business-logic tests
* Django Admin interface for managing users and tickets

## Ticket Lifecycle

```text
OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED
```

Status transitions are controlled by the service layer. Invalid transitions are rejected.

## User Roles

| Role          | Responsibilities                             |
| ------------- | -------------------------------------------- |
| ADMIN         | Assign tickets and manage all tickets        |
| SUPPORT_AGENT | View and work on tickets assigned to them    |
| CLIENT        | Create and manage their own eligible tickets |

## Project Structure

```text
enterprise-ticket-api/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── tickets/
│   ├── migrations/
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_tickets.py
│   │   ├── test_permissions.py
│   │   ├── test_lifecycle.py
│   │   └── test_api_endpoints.py
│   ├── admin.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── services.py
│   ├── urls.py
│   └── views.py
├── manage.py
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd enterprise-ticket-api
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create an admin user

```bash
python manage.py createsuperuser
```

Follow the prompts to create the administrator account.

### 7. Start the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

The Django Admin panel is available at:

```text
http://127.0.0.1:8000/admin/
```

## Authentication

The API uses JWT authentication.

### Login

```text
POST /api/auth/login/
```

Example request:

```json
{
    "username": "client1",
    "password": "your-password"
}
```

The response contains:

* Access token
* Refresh token
* User ID
* Username
* Email
* Application role

For protected endpoints, include the access token:

```text
Authorization: Bearer <access_token>
```

### Refresh Token

```text
POST /api/auth/refresh/
```

Example request:

```json
{
    "refresh": "<refresh_token>"
}
```

## API Endpoints

### Authentication

| Method | Endpoint             | Access | Description                          |
| ------ | -------------------- | ------ | ------------------------------------ |
| POST   | `/api/auth/login/`   | Public | Obtain JWT access and refresh tokens |
| POST   | `/api/auth/refresh/` | Public | Refresh an access token              |

### Tickets

| Method | Endpoint                    | Access                  | Description                              |
| ------ | --------------------------- | ----------------------- | ---------------------------------------- |
| GET    | `/api/tickets/`             | Authenticated           | List tickets visible to the current user |
| POST   | `/api/tickets/create/`      | CLIENT                  | Create a new ticket                      |
| POST   | `/api/tickets/<id>/assign/` | ADMIN                   | Assign a ticket to a support agent       |
| PATCH  | `/api/tickets/<id>/status/` | ADMIN / Assigned Agent  | Update ticket status                     |
| PATCH  | `/api/tickets/<id>/update/` | Authorized User         | Update editable ticket fields            |
| DELETE | `/api/tickets/<id>/`        | ADMIN / Eligible CLIENT | Delete a ticket                          |

## Ticket Creation

Clients can create tickets using:

```text
POST /api/tickets/create/
```

Example request:

```json
{
    "ticket_id": "TCK-001",
    "issue": "Database connection failure",
    "category": "database",
    "is_priority": true,
    "comment": "Application is unable to connect to the database."
}
```

The ticket client is automatically assigned from the authenticated user.

New tickets start with:

```text
OPEN
```

The client cannot directly set:

* Status
* Client
* Assigned agent
* Created timestamp
* Updated timestamp
* Resolved timestamp

## Ticket Assignment

Only administrators can assign tickets.

```text
POST /api/tickets/<id>/assign/
```

Example request:

```json
{
    "assigned_to": 3
}
```

The selected user must have the `SUPPORT_AGENT` role.

A successful assignment changes the ticket lifecycle from:

```text
OPEN → ASSIGNED
```

## Ticket Status Updates

Administrators can update any ticket status.

Support agents can update the status only for tickets assigned to them.

```text
PATCH /api/tickets/<id>/status/
```

Example:

```json
{
    "status": "IN_PROGRESS"
}
```

Only valid lifecycle transitions are accepted.

For example:

```text
ASSIGNED → IN_PROGRESS
IN_PROGRESS → RESOLVED
RESOLVED → CLOSED
```

Invalid transitions such as:

```text
OPEN → CLOSED
OPEN → RESOLVED
CLOSED → IN_PROGRESS
```

are rejected.

When a ticket becomes `RESOLVED`, the `resolved_at` timestamp is recorded.

## Ticket Updates

Authorized users can update editable ticket information:

```text
PATCH /api/tickets/<id>/update/
```

Example:

```json
{
    "issue": "Updated database connection failure",
    "category": "database",
    "is_priority": true,
    "comment": "Additional troubleshooting information."
}
```

Protected fields such as status, client, assignment, and timestamps cannot be modified through this endpoint.

## Ticket Visibility

Ticket visibility is role-based.

### ADMIN

Can view all tickets.

### SUPPORT_AGENT

Can view tickets assigned to them.

### CLIENT

Can view tickets created by them.

This filtering is applied at the queryset level before pagination, filtering, and search.

## Ticket Deletion

```text
DELETE /api/tickets/<id>/
```

Deletion rules:

* ADMIN can delete tickets.
* CLIENT can delete their own tickets only while they are `OPEN`.
* SUPPORT_AGENT cannot delete tickets.

## Filtering

Tickets can be filtered using query parameters.

Filter by status:

```text
GET /api/tickets/?status=OPEN
```

Filter by category:

```text
GET /api/tickets/?category=database
```

Filter by priority:

```text
GET /api/tickets/?is_priority=true
```

## Search

Tickets can be searched using:

```text
GET /api/tickets/?search=database
```

Search supports:

* Ticket ID
* Issue description
* Category

## Pagination

The API returns 10 tickets per page by default.

Example:

```text
GET /api/tickets/?page=2
```

Filtering, searching, and pagination can be combined:

```text
GET /api/tickets/?status=OPEN&search=database&page=2
```

## Testing

The project includes automated tests covering authentication, ticket creation, permissions, lifecycle rules, and API behavior.

Run the complete test suite with:

```bash
python manage.py test
```

The test suite covers:

* JWT authentication
* Authenticated ticket creation
* Unauthenticated access restrictions
* Role-based permissions
* Ticket assignment
* Ticket status authorization
* Valid ticket lifecycle transitions
* Invalid lifecycle transitions
* `resolved_at` timestamp handling
* Role-based ticket visibility
* API endpoint behavior
* Pagination behavior

## Development Notes

The project separates responsibilities across different layers:

* **Models** — Define users, roles, tickets, and ticket statuses.
* **Serializers** — Validate and transform API input/output.
* **Permissions** — Handle role-based and object-level authorization.
* **Services** — Contain ticket lifecycle and business rules.
* **Views** — Handle HTTP requests and API responses.
* **Tests** — Verify authentication, authorization, business logic, and API behavior.

This separation keeps business rules independent from the API layer and makes them easier to test.

## Future Improvements

Potential improvements include:

* PostgreSQL database support
* Docker containerization
* API documentation with OpenAPI/Swagger
* Automated CI/CD pipeline
* Structured application logging
* Email or notification integration
* Production deployment configuration

## License

This project is intended as a portfolio and learning project.
