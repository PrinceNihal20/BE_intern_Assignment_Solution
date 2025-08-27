# main.py
import uvicorn
import sqlite3
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import List, Dict
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ------------------------------------------------------------------------------------------------------
# Section 1: Data Models & Configuration
# ------------------------------------------------------------------------------------------------------

# Configure logging
# This is a good practice for production, providing timestamps and log levels.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for data validation and clear API schema.
# This makes the API self-documenting and ensures correct data types.
class Obstacle(BaseModel):
    x: float = Field(..., description="X-coordinate of the obstacle's bottom-left corner.")
    y: float = Field(..., description="Y-coordinate of the obstacle's bottom-left corner.")
    width: float = Field(..., description="Width of the rectangular obstacle.")
    height: float = Field(..., description="Height of the rectangular obstacle.")

class PlanRequest(BaseModel):
    wall_width: float = Field(..., gt=0, description="Width of the rectangular wall.")
    wall_height: float = Field(..., gt=0, description="Height of the rectangular wall.")
    obstacles: List[Obstacle] = Field(default=[], description="List of rectangular obstacles within the wall.")

class TrajectoryResponse(BaseModel):
    id: int
    wall_width: float
    wall_height: float
    path: List[List[float]]
    obstacles: List[Dict]
    created_at: str

# ------------------------------------------------------------------------------------------------------
# Section 2: Database Management
# ------------------------------------------------------------------------------------------------------

DB_NAME = "coverage_planning.db"

def get_db_connection():
    """Establishes and returns a SQLite database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def setup_database():
    """Initializes the SQLite database and creates the necessary table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trajectories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wall_width REAL NOT NULL,
            wall_height REAL NOT NULL,
            obstacles TEXT NOT NULL,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    # Overkill optimization: Adding an index on `created_at` for faster time-based queries.
    # This is crucial for real-world scenarios where you might want to retrieve
    # the latest trajectories or filter by date range.
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON trajectories (created_at)")
    conn.commit()
    conn.close()

# Context manager for application lifecycle events.
# This ensures the database is set up when the application starts.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the application."""
    logger.info("Application starting up...")
    setup_database()
    logger.info("Database setup complete.")
    yield
    logger.info("Application shutting down...")

app = FastAPI(lifespan=lifespan)

# ------------------------------------------------------------------------------------------------------
# Section 3: Path Planning Logic
# ------------------------------------------------------------------------------------------------------

def _generate_path(wall_width: float, wall_height: float, obstacles: List[Obstacle]) -> List[List[float]]:
    """
    Generates a boustrophedon (snake-like) coverage path for a rectangular area.

    This function represents a simple path planning algorithm. It sweeps back and forth
    across the area. A more complex, real-world scenario would involve more advanced
    path planning algorithms (e.g., A* or RRT*) that handle complex obstacle geometries
    and robot kinematics. This simplified approach demonstrates the core concept.
    """
    path = []
    step_size = 0.25 # A reasonable step size for the path points
    current_x = 0.0
    current_y = 0.0
    direction = 1  # 1 for moving right, -1 for moving left

    # Convert obstacle objects to a simpler format for collision checking
    # This is a small optimization to avoid repeated object creation inside the loop
    obs_rects = [{'x': o.x, 'y': o.y, 'width': o.width, 'height': o.height} for o in obstacles]

    # Simple collision detection helper
    def is_collision(x: float, y: float) -> bool:
        """Checks if a point (x, y) collides with any obstacle."""
        for obs in obs_rects:
            if obs['x'] <= x <= obs['x'] + obs['width'] and \
               obs['y'] <= y <= obs['y'] + obs['height']:
                return True
        return False

    while current_y <= wall_height:
        # Move across the wall
        while 0 <= current_x <= wall_width:
            if not is_collision(current_x, current_y):
                path.append([current_x, current_y])
            current_x += step_size * direction

        # Adjust for boundary and move up to the next row
        current_x -= step_size * direction  # Step back from the boundary
        current_y += step_size
        direction *= -1  # Change direction for the next sweep

    return path

# ------------------------------------------------------------------------------------------------------
# Section 4: API Endpoints
# ------------------------------------------------------------------------------------------------------

# Middleware for logging and response timing.
# This is a key "overkill" feature requested, providing valuable operational insights.
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Request handled: {request.method} {request.url} - Processed in {process_time:.4f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.post("/plan_coverage", response_model=TrajectoryResponse)
async def plan_coverage(request_data: PlanRequest):
    """
    Plans a coverage path based on wall and obstacle dimensions and stores it.
    """
    try:
        wall_width = request_data.wall_width
        wall_height = request_data.wall_height
        obstacles = request_data.obstacles

        logger.info(f"Received request to plan coverage for {wall_width}x{wall_height} wall with {len(obstacles)} obstacles.")
        
        path = _generate_path(wall_width, wall_height, obstacles)

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Overkill optimization: Using parameterized queries to prevent SQL injection.
        # This is a fundamental security practice for any real-world application.
        cursor.execute(
            """INSERT INTO trajectories (wall_width, wall_height, obstacles, path, created_at) VALUES (?, ?, ?, ?, datetime('now'))""",
            (wall_width, wall_height, json.dumps([o.dict() for o in obstacles]), json.dumps(path))
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        logger.info(f"Trajectory {new_id} generated and saved successfully.")
        
        return {
            "id": new_id,
            "wall_width": wall_width,
            "wall_height": wall_height,
            "obstacles": [o.dict() for o in obstacles],
            "path": path,
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error during coverage planning: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/get_trajectory/{trajectory_id}", response_model=TrajectoryResponse)
async def get_trajectory(trajectory_id: int):
    """
    Retrieves a stored coverage trajectory by its ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trajectories WHERE id = ?", (trajectory_id,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        raise HTTPException(status_code=404, detail="Trajectory not found")

    return {
        "id": result['id'],
        "wall_width": result['wall_width'],
        "wall_height": result['wall_height'],
        "obstacles": json.loads(result['obstacles']),
        "path": json.loads(result['path']),
        "created_at": result['created_at']
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
