# test_main.py
import pytest
import time
from fastapi.testclient import TestClient
from main import app, setup_database, DB_NAME
import os

# Create a temporary test database before running tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Sets up a clean database for testing and cleans it up afterwards."""
    # Use a separate database file to avoid conflicts with the main application
    test_db_name = "test_db.db"
    
    # Overkill optimization: Use a context manager or a dedicated setup/teardown
    # fixture to ensure the test database is created and destroyed correctly.
    # This prevents side effects between tests.
    
    # Temporarily change the DB_NAME for the test session
    global DB_NAME
    original_db_name = DB_NAME
    DB_NAME = test_db_name
    
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    setup_database()
    
    yield
    
    # Clean up after all tests are finished
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        
    # Restore the original DB_NAME
    DB_NAME = original_db_name

client = TestClient(app)

# ------------------------------------------------------------------------------------------------------
# API Tests
# ------------------------------------------------------------------------------------------------------

def test_plan_coverage_success():
    """
    Tests the successful creation of a new coverage plan.
    """
    response = client.post(
        "/plan_coverage",
        json={
            "wall_width": 10.0,
            "wall_height": 10.0,
            "obstacles": [
                {"x": 4.0, "y": 4.0, "width": 2.0, "height": 2.0}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "path" in data
    assert len(data["path"]) > 0
    assert data["wall_width"] == 10.0
    assert len(data["obstacles"]) == 1

def test_get_trajectory_success():
    """
    Tests the successful retrieval of a previously created trajectory.
    """
    # First, create a trajectory to ensure one exists
    post_response = client.post(
        "/plan_coverage",
        json={
            "wall_width": 5.0,
            "wall_height": 5.0,
            "obstacles": []
        }
    )
    assert post_response.status_code == 200
    trajectory_id = post_response.json()["id"]

    # Now, try to get it
    get_response = client.get(f"/get_trajectory/{trajectory_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == trajectory_id
    assert data["wall_width"] == 5.0
    assert "path" in data
    assert "obstacles" in data

def test_get_trajectory_not_found():
    """
    Tests that the API correctly returns a 404 for a non-existent trajectory ID.
    """
    response = client.get("/get_trajectory/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Trajectory not found"

def test_api_performance():
    """
    Tests the response time of the API. This is part of the "overkill" request.
    A simple performance check to ensure it meets a basic SLA (Service Level Agreement).
    """
    start_time = time.time()
    response = client.post(
        "/plan_coverage",
        json={
            "wall_width": 20.0,
            "wall_height": 20.0,
            "obstacles": [
                {"x": 10, "y": 10, "width": 1, "height": 1}
            ]
        }
    )
    end_time = time.time()
    assert response.status_code == 200
    # The response time should be under 1 second for this small-scale problem
    # In a real-world scenario, this limit would be based on specific requirements.
    assert (end_time - start_time) < 1.0

def test_api_with_multiple_obstacles():
    """
    Tests the API with a more complex scenario involving multiple obstacles.
    """
    response = client.post(
        "/plan_coverage",
        json={
            "wall_width": 15.0,
            "wall_height": 15.0,
            "obstacles": [
                {"x": 2.0, "y": 2.0, "width": 3.0, "height": 3.0},
                {"x": 10.0, "y": 10.0, "width": 2.0, "height": 2.0},
                {"x": 7.0, "y": 12.0, "width": 1.0, "height": 1.0}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["obstacles"]) == 3
    assert len(data["path"]) > 0
