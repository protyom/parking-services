# Parking Services Monitoring System

AI-powered parking monitoring system that uses computer vision to detect available parking spaces in real-time from camera feeds.

## Features

- **Real-time Parking Detection**: Uses YOLOv8 to detect cars from multiple camera feeds
- **Multi-section Support**: Monitor multiple parking sections/zones with configurable polygons
- **REST API**: Query current parking availability via HTTP endpoints
- **Automated Monitoring**: Celery tasks automatically update parking states every 2 minutes
- **Scalable Architecture**: Docker-based deployment with PostgreSQL and Redis
- **API Key Authentication**: Secure API access with django-rest-framework-api-key

## Technologies

- **Backend**: Django 5.0 + Django REST Framework
- **Computer Vision**: YOLOv8 (Ultralytics), OpenCV, PIL
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL
- **Deployment**: Docker Compose
- **Python**: 3.12+

## Installation

### Prerequisites

- Python 3.12 or higher
- PostgreSQL 16
- Redis
- (Optional) Docker and Docker Compose

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd parking_services
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[django,training]"
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:

   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/parking_db
   WORKER_DATABASE_URL=postgresql://user:password@localhost:5432/parking_db
   POSTGRES_USER=user
   POSTGRES_DB=parking_db
   POSTGRES_PASSWORD=password
   POSTGRES_PORT=5432

   # Redis
   REDIS_ADDR=127.0.0.1
   REDIS_PORT=6379
   REDIS_PASSWORD=your_redis_password

   # Django
   SECRET_KEY=your-secret-key-here-change-this-in-production
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # YOLO Model
   YOLO_PATH=/path/to/yolov8x.pt

   # Camera Configuration (JSON)
   CAMERA_CONF={"cameras":[{"connection":"rtsp://camera1","sections":[{"name":"section_a","verbose_name":"Section A","capacity":20,"polygon":[[100,100],[200,100],[200,200],[100,200]]}]}]}
   ```

   **Generate a secure SECRET_KEY for production:**
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```
   Copy the output and use it as your `SECRET_KEY` in `.env`.

5. **Download YOLOv8 model**
   ```bash
   # Download pre-trained YOLOv8 model
   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8x.pt
   ```

6. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

7. **Initialize parking sections**
   ```bash
   python manage.py init_sections
   ```

8. **Create API key**

   Start Django shell:
   ```bash
   python manage.py shell
   ```

   Then run the following Python commands:
   ```python
   from rest_framework_api_key.models import APIKey
   api_key, key = APIKey.objects.create_key(name="my-api-key")
   print(key)  # Save this key securely
   ```

## Usage

### Running the Development Server

**Start Django server:**

```bash
python manage.py runserver
```

**Start Celery worker (in separate terminal):**

```bash
celery -A parking_services worker -l INFO --concurrency=4
```

**Start Celery beat scheduler (in separate terminal):**

```bash
celery -A parking_services beat
# Or use: sh bin/run_beat.sh
```

### Docker Deployment

1. **Build and start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Initialize the database:**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py init_sections
   ```

3. **Access the application:**
   - API: `http://localhost:8080/api/`
   - Admin: `http://localhost:8080/admin/`

4. **View logs:**
   ```bash
   docker-compose logs -f web
   docker-compose logs -f celery
   ```

## API Documentation

### Authentication

All API endpoints require an API key. Include the key in the request header:

```http
Authorization: Api-Key YOUR_API_KEY_HERE
```

### Endpoints

#### Get Current Parking State

**GET** `/api/v1/parking-state/`

Returns the most recent parking availability for all sections.

**Response:**
```json
{
  "phrase": "Section A - 15, Section B - 8, Section C - 22",
  "data": [
    {
      "section": {
        "name": "section_a",
        "verbose_name": "Section A",
        "capacity": 20
      },
      "free_places": 15,
      "created_photo_at": "2024-05-26T10:30:00Z"
    },
    {
      "section": {
        "name": "section_b",
        "verbose_name": "Section B",
        "capacity": 10
      },
      "free_places": 8,
      "created_photo_at": "2024-05-26T10:30:00Z"
    }
  ]
}
```

**Example:**
```bash
curl -H "Authorization: Api-Key YOUR_API_KEY" http://localhost:8080/api/v1/parking-state/
```

## Configuration

### Camera Configuration

Define cameras and parking sections in the `CAMERA_CONF` environment variable as JSON:

```json
{
  "cameras": [
    {
      "connection": "rtsp://192.168.1.100:554/stream",
      "sections": [
        {
          "name": "section_a",
          "verbose_name": "Section A - Main Entrance",
          "capacity": 20,
          "polygon": [
            [100, 100],
            [400, 100],
            [400, 300],
            [100, 300]
          ]
        },
        {
          "name": "section_b",
          "verbose_name": "Section B - North Side",
          "capacity": 15,
          "polygon": [
            [450, 100],
            [700, 100],
            [700, 300],
            [450, 300]
          ]
        }
      ]
    }
  ]
}
```

**Configuration Fields:**

- `connection`: Camera URL (RTSP, HTTP, or local file path)
- `name`: Unique identifier for the parking section
- `verbose_name`: Human-readable section name
- `capacity`: Maximum number of parking spaces
- `polygon`: Array of `[x, y]` coordinates defining the section boundaries in the camera frame

### Monitoring Frequency

The system checks parking availability every 2 minutes by default. To change this, modify the crontab schedule in `parking_services/celery.py`:

```python
CELERYBEAT_SCHEDULE = {
    'actualize-parking-state': {
        'task': 'parking_services.core.tasks.update_parking_places',
        'schedule': crontab(minute="*/2"),  # Change this
    },
}
```

## Development


### Project Structure

```text
parking_services/
├── parking_services/
│   ├── api/                  # REST API endpoints
│   │   └── v1/               # API version 1
│   │       ├── views/        # ViewSets
│   │       └── serializers/
│   ├── core/                 # Core business logic
│   │   ├── models.py         # Database models
│   │   ├── tasks.py          # Celery tasks
│   │   ├── vision/           # Computer vision components
│   │   │   └── camera.py     # Camera and detection logic
│   │   └── management/
│   │       └── commands/     # Custom Django commands
│   ├── settings.py           # Django settings
│   ├── celery.py             # Celery configuration
│   └── urls.py               # URL routing
├── docker-compose.yml        # Docker services
├── manage.py                 # Django CLI
└── pyproject.toml            # Project dependencies
```

### Django Management Commands

**Initialize parking sections from configuration:**

```bash
python manage.py init_sections
```

**Manually trigger parking state update:**

```bash
python manage.py start_task
```

**Run tests:**

```bash
python manage.py test
```

### Virtual Environments

The project provides three separate environments:

- `.venv` - Base Django development
- `.venv-full` - Full stack with ML training dependencies
- `.venv-training` - YOLOv8 training only (lightweight for embedded devices)

Activate the appropriate environment for your use case:

```bash
source .venv/bin/activate              # Django development
source .venv-full/bin/activate         # Full stack with training
source .venv-training/bin/activate     # Training only
```

## How It Works

1. **Celery beat** triggers the `update_parking_places` task every 2 minutes
2. **Camera capture**: System retrieves frames from configured camera feeds via OpenCV
3. **Object detection**: YOLOv8 model identifies cars in each frame (class ID 2)
4. **Spatial matching**: Car bounding box centers are matched to parking sections using polygon intersection (sympy)
5. **State calculation**: Free spaces = section capacity - detected cars
6. **Database update**: New `ParkingState` records are bulk-created
7. **API access**: REST API returns the latest parking states across all sections

## Troubleshooting

### Camera Connection Issues

- Verify camera URLs are accessible from the server
- Check RTSP credentials and network connectivity
- Test camera feed with VLC or similar tool

### Detection Accuracy

- Ensure parking section polygons accurately cover the parking areas in camera frames
- Adjust YOLOv8 confidence threshold in `tasks.py` (default: 0.3)
- Verify lighting conditions and camera angles

### Celery Tasks Not Running

- Check Redis connectivity: `redis-cli -a <password> ping`
- Verify Celery worker is running: `docker-compose logs celery`
- Check beat scheduler status: `docker-compose logs celerybeat`

### Database Issues

- Ensure migrations are applied: `python manage.py migrate`
- Verify PostgreSQL is running and accessible
- Check `DATABASE_URL` environment variable

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
