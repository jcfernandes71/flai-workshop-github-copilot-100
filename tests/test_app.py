"""
Tests for the Mergington High School Activities API.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participants to a known state before each test."""
    original = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, participants in original.items():
        activities[name]["participants"] = participants


client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_all_activities(self):
        response = client.get("/activities")
        data = response.json()
        assert len(data) > 0

    def test_activity_has_required_fields(self):
        response = client.get("/activities")
        data = response.json()
        for activity in data.values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self):
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self):
        email = "addme@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email in participants

    def test_signup_unknown_activity_returns_404(self):
        response = client.post(
            "/activities/NonExistent/signup?email=x@mergington.edu"
        )
        assert response.status_code == 404

    def test_signup_duplicate_returns_400(self):
        email = "duplicate@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 400

    def test_signup_full_activity_returns_400(self):
        activity_name = "Chess Club"
        activity = activities[activity_name]
        # Fill up remaining spots
        for i in range(activity["max_participants"] - len(activity["participants"])):
            client.post(f"/activities/{activity_name}/signup?email=fill{i}@mergington.edu")
        response = client.post(
            f"/activities/{activity_name}/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self):
        # First sign up, then unregister
        email = "temp@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        response = client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_unregister_removes_participant(self):
        email = "remove@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert email not in participants

    def test_unregister_unknown_activity_returns_404(self):
        response = client.delete(
            "/activities/NonExistent/unregister?email=x@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_not_signed_up_returns_400(self):
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=nothere@mergington.edu"
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET / (redirect)
# ---------------------------------------------------------------------------

class TestRoot:
    def test_root_redirects(self):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307, 308)
        assert "/static/index.html" in response.headers["location"]
