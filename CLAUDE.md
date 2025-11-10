# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a parking monitoring system that uses YOLOv8 computer vision to detect cars in parking sections via camera feeds. The system consists of:
- Django REST API for querying parking availability
- Celery workers that periodically analyze camera feeds
- PostgreSQL database for storing parking states
- Redis for Celery broker and caching

## Architecture

### Core Components

**parking_services/core/**
- `models.py`: Defines `ParkingSection` (parking areas with capacity) and `ParkingState` (snapshots of free spaces)
- `tasks.py`: Celery task `update_parking_places()` that runs every 2 minutes to analyze camera feeds
- `vision/camera.py`:
  - `Camera`: Captures frames from camera feeds, divides detections into parking sectors using polygon boundaries
  - `CameraCluster`: Manages multiple cameras and aggregates results
  - `Sector`: Represents a parking section with polygon boundaries for spatial matching

**parking_services/api/**
- REST API versioned as v1
- `v1/views/parking_state.py`: `ParkingStateViewSet` returns most recent parking states across all sections
- API uses django-rest-framework-api-key for authentication

### Data Flow

1. Celery beat triggers `update_parking_places()` task every 2 minutes
2. Task reads camera configuration from `settings.CAMERA_CONF` (JSON with camera connections and section polygons)
3. Each camera captures a frame via OpenCV
4. YOLOv8 model (path from `settings.YOLO_PATH`) runs inference on all frames
5. Detections with class=2 (cars) are matched to parking sections via polygon intersection
6. `ParkingState` records are bulk created with free_places = capacity - car_count
7. API returns latest states grouped by timestamp

### Configuration

Camera configuration is loaded from environment variable `CAMERA_CONF` as JSON:
```json
{
  "cameras": [
    {
      "connection": "rtsp://...",
      "sections": [
        {
          "name": "section_a",
          "verbose_name": "Section A",
          "capacity": 20,
          "polygon": [[x1,y1], [x2,y2], ...]
        }
      ]
    }
  ]
}
```

Database connection uses `django-environ` via `DATABASE_URL` environment variable.

## Development Commands

### Virtual Environment

Three separate environments are available:
- `.venv` - Base Django development
- `.venv-full` - Full stack with training dependencies
- `.venv-training` - YOLOv8 training only

Activate with: `source .venv/bin/activate`

### Running the Application

**Start Django development server:**
```bash
python manage.py runserver
```

**Database migrations:**
```bash
python manage.py migrate
python manage.py makemigrations
```

**Initialize parking sections from config:**
```bash
python manage.py init_sections
```

**Celery worker:**
```bash
celery -A parking_services worker -E -l INFO --concurrency=4
```

**Celery beat scheduler:**
```bash
celery -A parking_services beat
```
Or use: `sh bin/run_beat.sh`

### Docker Deployment

**Start all services:**
```bash
docker-compose up
```

Services defined:
- `db_postgres`: PostgreSQL database
- `web`: Django app (port 8080 mapped to container port 80)
- `redis`: Redis broker
- `celerybeat`: Scheduler
- `celery`: Task worker (uses host network mode)

**Environment variables required in `.env`:**
- `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`
- `REDIS_PASSWORD`
- `APP_IMAGE` (Docker image name)
- `DATABASE_URL`, `WORKER_DATABASE_URL`
- `ALLOWED_HOSTS`
- `CAMERA_CONF` (JSON string)
- `YOLO_PATH` (path to .pt model file)

### Testing

No test suite currently configured. The project includes placeholder test files.

## Key Implementation Details

### Parking Detection Logic

The system uses polygon-based spatial matching:
1. YOLOv8 detects bounding boxes for cars (class ID 2)
2. Calculate center point of each bounding box
3. Check which parking section polygon encloses the center point using `sympy.Polygon.encloses()`
4. Increment car_count for matching section
5. Calculate free_places = capacity - car_count

### API Response Format

`GET /api/v1/parking-state/` returns:
```json
{
  "phrase": "Section A - 15, Section B - 8",
  "data": [
    {
      "section": {"name": "section_a", "verbose_name": "Section A"},
      "free_places": 15,
      "created_photo_at": "2024-05-26T10:30:00Z"
    }
  ]
}
```

The endpoint filters for states with the latest `created_photo_at` timestamp (within 1 second to handle simultaneous captures).

### Celery Configuration

- Broker: Redis at `redis://:password@host:port/0`
- Result backend: Redis database 1
- Beat schedule: Every 2 minutes (`crontab(minute="*/2")`)
- Accepts pickle and JSON serialization
- Worker concurrency: 4

## Project Dependencies

Core packages (from `pyproject.toml`):
- **django**: Django REST framework stack with API key auth
- **training**: ultralytics (YOLOv8), torch, torchvision, jupyter, pandas, scikit-learn
- **orangepi**: Lightweight deployment (ultralytics + opencv-headless)

The project uses `pyproject.toml` with optional dependency groups for different deployment scenarios.
