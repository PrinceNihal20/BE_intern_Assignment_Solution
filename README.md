## Coverage Planning & Data Management
This project provides a full-stack solution for a coverage planning and data management system, developed for a industry internship.

The solution is composed of three main parts: a FastAPI backend, a web-based frontend visualization, and a Pytest suite for API validation.

## Project Objectives & Fulfillment Objective and Implementation Details

# Coverage Planning
The _generate_path function in main.py uses a simple boustrophedon (snake-like) algorithm to generate a complete path. The algorithm intelligently handles and avoids user-defined rectangular obstacles.

# Backend Data Management
A FastAPI application manages a SQLite database with a trajectories table. Basic indexing on the created_at column is implemented for query optimization, and logging middleware provides performance insights.

# Frontend Visualization
The index.html file uses a standard HTML <canvas> element to render a 2D visualization of the path. It includes a trajectory playback feature and a clear, dynamic explanation of the path planning logic.

# Testing
A comprehensive pytest suite is included to validate endpoint functionality and response times. The tests use a separate temporary database to ensure they are isolated and reliable.

## Key Technical Decisions
FastAPI & Python: Chosen for its high performance, excellent documentation, and built-in features for data validation (Pydantic models) and testing.

SQLite: A lightweight, serverless database ideal for a small-scale application. Its file-based nature simplifies the setup and data management.

Boustrophedon Algorithm: A foundational path planning algorithm used to demonstrate a simple yet effective approach to coverage. More complex applications would use advanced algorithms like A* or RRT* for more intricate scenarios.

Secure & Optimized Code: Key production-like features were implemented, including database indexing, parameterized queries to prevent SQL injection, and a logging middleware to track request performance.

Video Walkthrough
[<span style="color:red">https://drive.google.com/file/d/12fUDX0DFRkyHIDHtzsfeK-8TUoDmgxWL/view?usp=sharing</span>]

This short video provides a detailed walkthrough of the application, explaining the core logic, user interaction flow, and the reasoning behind the technical decisions.

How to Run the Application
Follow these steps to set up and run the project locally.


Set Up the Python Environment:

# Create a virtual environment
python -m venv venv

# Activate the environment
# On macOS/Linux
source venv/bin/activate
# On Windows
venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn "uvicorn[standard]" pytest requests httpx

Start the Backend Server:

uvicorn main:app --reload

The server will be running at http://127.0.0.1:8000.

# Open the Frontend:
Open the index.html file in your web browser. The frontend will automatically connect to the running backend.

# Run the Tests:
Open a new terminal, activate the virtual environment, and run the tests.
 pytest
