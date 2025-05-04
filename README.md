# GPP Portal FastAPI Backend

This is a FastAPI implementation of the GPP Portal backend, designed as a drop-in replacement for the Express TypeScript backend while using PostgreSQL instead of MongoDB.

## Features

- **FastAPI Framework**: High performance, easy to learn, fast to code, ready for production
- **PostgreSQL Database**: Robust relational database with SQLAlchemy ORM
- **JWT Authentication**: Secure authentication with role-based access control
- **Automatic API Documentation**: Interactive API documentation with Swagger/OpenAPI
- **Database Migrations**: Managed database schema changes with Alembic
- **CSV Import/Export**: Convenient data management with CSV imports and exports
- **Input Validation**: Request validation with Pydantic
- **Dependency Injection**: Clean and testable codebase
- **Error Handling**: Consistent error responses

## Prerequisites

- Python 3.8+
- PostgreSQL 12+

## Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd fastapi-backend
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:

   Create a `.env` file in the root directory by copying the template:

   ```bash
   cp .env.template .env
   ```

   Then edit the `.env` file to set your specific configurations.

5. **Create the database**:

   ```bash
   # Using psql
   psql -U postgres -c "CREATE DATABASE gpp_portal;"
   ```

6. **Run database migrations**:

   ```bash
   python scripts/create_migration.py
   ```

7. **Seed initial data** (optional):

   ```bash
   python scripts/seed_db.py
   ```

## Running the Application

### Using Python directly

```bash
# Development mode with auto-reload
python run.py --reload

# Production mode
python run.py
```

### Using Docker Compose

For development with hot-reload:

```bash
docker-compose -f docker-compose.dev.yml up
```

For production:

```bash
docker-compose up -d
```

## Accessing the API

- **API Base URL**: <http://localhost:9000/api>
- **API Documentation**: <http://localhost:9000/api/docs>
- **ReDoc Documentation**: <http://localhost:9000/api/redoc>
- **PgAdmin** (if using Docker): <http://localhost:5050>

## Project Structure

```
fastapi-backend/
├── alembic/              # Database migrations
├── app/
│   ├── api/              # API routes (auth, users, departments, etc.)
│   ├── middleware/       # Auth and error handling middleware
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic validation schemas
│   ├── services/         # Business logic
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection
│   └── main.py           # FastAPI application
├── scripts/              # Utility scripts
├── tests/                # Test files
├── uploads/              # Upload directory for files
├── .env                  # Environment variables (create this)
├── .env.template         # Environment variables template
├── docker-compose.yml    # Docker Compose for production
├── docker-compose.dev.yml# Docker Compose for development
├── Dockerfile            # Docker build configuration
├── alembic.ini           # Alembic configuration
├── requirements.txt      # Python dependencies
└── run.py                # Application runner script
```

## API Endpoints

The API maintains the same interface as the Express version to ensure compatibility with existing frontend applications.

### Authentication

- `POST /api/auth/login` - Login with email and password
- `POST /api/auth/signup` - Register a new user
- `POST /api/auth/switch-role` - Switch user role

### Users

- `GET /api/users/me` - Get current user
- `PATCH /api/users/updateMe` - Update current user
- `GET /api/users` - Get all users (admin)
- `POST /api/users` - Create a new user (admin)
- `GET /api/users/{user_id}` - Get a specific user (admin)
- `PATCH /api/users/{user_id}` - Update a user (admin)
- `DELETE /api/users/{user_id}` - Delete a user (admin)
- `POST /api/users/import` - Import users from CSV (admin)
- `GET /api/users/export` - Export users to CSV (admin)

### Departments

- `GET /api/departments` - Get all departments
- `POST /api/departments` - Create a new department
- `GET /api/departments/stats` - Get department statistics
- `POST /api/departments/import` - Import departments from CSV
- `GET /api/departments/export` - Export departments to CSV
- `GET /api/departments/{department_id}` - Get a specific department
- `PATCH /api/departments/{department_id}` - Update a department
- `DELETE /api/departments/{department_id}` - Delete a department

### Faculty

- `GET /api/faculty` - Get all faculty members
- `POST /api/faculty` - Create a new faculty member
- `GET /api/faculty/export-csv` - Export faculty to CSV
- `POST /api/faculty/upload-csv` - Import faculty from CSV
- `GET /api/faculty/{faculty_id}` - Get a specific faculty member
- `PATCH /api/faculty/{faculty_id}` - Update a faculty member
- `DELETE /api/faculty/{faculty_id}` - Delete a faculty member
- `GET /api/faculty/department/{department_id}` - Get faculty by department

### Students

- `GET /api/students` - Get all students
- `POST /api/students` - Create a new student
- `POST /api/students/sync` - Sync student users
- `GET /api/students/export-csv` - Export students to CSV
- `POST /api/students/upload-csv` - Import students from CSV
- `GET /api/students/{student_id}` - Get a specific student
- `PATCH /api/students/{student_id}` - Update a student
- `DELETE /api/students/{student_id}` - Delete a student
- `GET /api/students/department/{department_id}` - Get students by department

### Admin

- `GET /api/admin/roles` - Get all roles
- `POST /api/admin/roles` - Create a new role
- `GET /api/admin/roles/{role_name}` - Get a specific role
- `PATCH /api/admin/roles/{role_name}` - Update a role
- `DELETE /api/admin/roles/{role_name}` - Delete a role
- `PATCH /api/admin/users/{user_id}/roles` - Assign roles to a user

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
