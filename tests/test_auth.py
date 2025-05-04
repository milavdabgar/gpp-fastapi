import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.services.init import initialize_database

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create a test client
client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    # Create the test database
    Base.metadata.create_all(bind=engine)
    
    # Initialize the database with default data
    db = TestingSessionLocal()
    initialize_database(db)
    db.close()
    
    yield
    
    # Clean up the database after tests
    Base.metadata.drop_all(bind=engine)

# Test health check
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

# Test login with non-existent user
def test_login_nonexistent_user(test_db):
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "password"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

# Test signup and login
def test_signup_and_login(test_db):
    # Sign up a new user
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "name": "Test User",
            "email": "test.user@example.com",
            "password": "Password123",
            "roles": ["student"]
        }
    )
    assert signup_response.status_code == 200
    assert signup_response.json()["status"] == "success"
    assert signup_response.json()["data"]["email"] == "test.user@example.com"
    
    # Try to log in with the new user
    login_response = client.post(
        "/api/auth/login",
        json={"email": "test.user@example.com", "password": "Password123"}
    )
    assert login_response.status_code == 200
    assert login_response.json()["status"] == "success"
    assert "access_token" in login_response.json()["data"]
    assert login_response.json()["data"]["token_type"] == "bearer"

# Test login and accessing protected route
def test_login_and_access_protected_route(test_db):
    # First create a test admin user if needed
    db = TestingSessionLocal()
    from app.models.user import User, Role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    
    admin_user = db.query(User).filter(User.email == "admin@gppalanpur.in").first()
    if not admin_user:
        admin_user = User(
            name="Admin User",
            email="admin@gppalanpur.in",
            roles=[admin_role],
            selected_role="admin"
        )
        admin_user.set_password("Admin@123")
        db.add(admin_user)
        db.commit()
    db.close()
    
    # Login with admin
    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@gppalanpur.in", "password": "Admin@123"}
    )
    assert login_response.status_code == 200
    
    # Get the token
    token = login_response.json()["data"]["access_token"]
    
    # Access a protected route (get current user)
    me_response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["email"] == "admin@gppalanpur.in"
    
    # Try to access without token
    no_token_response = client.get("/api/users/me")
    assert no_token_response.status_code == 401

# Test role switching
def test_role_switching(test_db):
    # Create a test user with multiple roles
    db = TestingSessionLocal()
    from app.models.user import User, Role
    student_role = db.query(Role).filter(Role.name == "student").first()
    faculty_role = db.query(Role).filter(Role.name == "faculty").first()
    
    user = db.query(User).filter(User.email == "multi.role@example.com").first()
    if not user:
        user = User(
            name="Multi Role User",
            email="multi.role@example.com",
            roles=[student_role, faculty_role],
            selected_role="student"
        )
        user.set_password("Password123")
        db.add(user)
        db.commit()
    db.close()
    
    # Login
    login_response = client.post(
        "/api/auth/login",
        json={"email": "multi.role@example.com", "password": "Password123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]
    
    # Check current role
    me_response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["data"]["selected_role"] == "student"
    
    # Switch role
    switch_response = client.post(
        "/api/auth/switch-role",
        json={"role": "faculty"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert switch_response.status_code == 200
    new_token = switch_response.json()["data"]["access_token"]
    
    # Check new role
    new_me_response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {new_token}"}
    )
    assert new_me_response.status_code == 200
    assert new_me_response.json()["data"]["selected_role"] == "faculty"