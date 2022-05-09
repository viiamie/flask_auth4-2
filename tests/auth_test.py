"""This tests the homepage"""

import pytest
from flask import session
from app.db.models import User

def test_request_main_menu_links(client):
    """This makes the index page"""
    response = client.get("/")
    assert response.status_code == 200
    assert b'href="/login"' in response.data
    assert b'href="/register"' in response.data

def test_auth_pages(client):
    """This makes the index page"""
    response = client.get("/dashboard")
    assert response.status_code == 302
    response = client.get("/register")
    assert response.status_code == 200
    response = client.get("/login")
    assert response.status_code == 200

def test_register_success(client):
    """This tests for successful registration"""
    assert client.get("register").status_code == 200
    # successful registration redirects to the login page
    response = client.post("register", data={"email": "email@email.com", "password": "0123456",
                                             "confirm": "0123456"})
    # checks if user is inserted in database
    with client.application.app_context():
        assert User.query.filter_by(email="email@email.com").first() is not None
    assert "/login" == response.headers["Location"]

def test_login_success(client):
    """This tests for successful login"""
    with client:
        assert client.get("/login").status_code == 200
        # successful login redirects to the dashboard
        response = client.post("/login", data={"email": "email@email.com", "password": "0123456"})
        assert "/dashboard" == response.headers["Location"]
        # check that the user is loaded from the session
        with client.application.app_context():
            user_id = User.query.filter_by(email="email@email.com").first().get_id()
        assert session['_user_id'] == user_id


def test_register_badPassword_matching(client):
    """This tests a bad password that does not match (registration)"""
    response = client.post("/register", data={"email": "test@email.com", "password": "0123456",
                                              "confirm": "0246810"}, follow_redirects=True)
    assert b"Passwords must match" in response.data

@pytest.mark.parametrize(
    ("email", "password", "confirm"),
    (("test@email.com", "abc", "abc"),
     ("test@email.com", "1", "1")),
)
def test_register_badPassword_criteria(client, email, password, confirm):
    """This tests a bad password that does not meet the criteria (registration)"""
    response = client.post("/register", data=dict(email=email, password=password, confirm=confirm),
                           follow_redirects=True)
    assert response.status_code == 200

def test_register_badEmail(client):
    """This tests an invalid email being used for registration"""
    response = client.post("/register", data={"email": "", "password": "0123456", "confirm": "0123456"}, follow_redirects=True)
    assert response.status_code == 200

def test_login_badEmail(client):
    """This tests logging in with invalid email"""
    response = client.post("/login", data={"email": "e", "password": "test0123", "confirm": "test0123"}, follow_redirects=True)
    assert b"Invalid username or password" in response.data

def test_login_badPassword(client):
    """This tests logging in with invalid password"""
    response = client.post("/login", data={"email": "email@email.com", "password": "wrongPassword"}, follow_redirects=True)
    assert b"Invalid username or password" in response.data

def test_already_registered(client):
    """This tests if the user is already registered"""
    assert client.get("register").status_code == 200
    response = client.post("register", data={"email": "email@email.com", "password": "0123456",
                                             "confirm": "0123456"})
    assert "/login" == response.headers["Location"]
    with client:
        response_2 = client.get("/login")
        assert b"Already Registered" in response_2.data

def test_logout_success(client):
    """This tests that the user logged out successfully"""
    client.post("/login", data={"email": "email@email.com", "password": "0123456"}, follow_redirects=True)
    with client:
        client.get("/logout")
        assert "_user_id" not in session

def test_dashboard_access(client):
    """This test allows access to the dashboard for logged-in users"""
    assert client.get("/login").status_code == 200
    response = client.post("/login", data={"email": "email@email.com", "password": "0123456"})
    assert "/dashboard" == response.headers["Location"]
    assert client.get("/dashboard").status_code == 200

def test_deny_dashboard_access(client):
    """This test denies access to the dashboard for users not logged-in"""
    response = client.get("/dashboard")
    assert "/login?next=%2Fdashboard" == response.headers["Location"]
    with client:
        response = client.get("/login")
        assert b"Please log in to access this page." in response.data