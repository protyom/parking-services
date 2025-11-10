# Docker Build and Deployment Guide

This document describes the Docker build process and deployment configurations for the Parking Services Monitoring System, including support for both x86_64 and ARM architectures.

## Table of Contents

- [Build Architecture](#build-architecture)
- [Multi-Stage Build Process](#multi-stage-build-process)
- [Building Images](#building-images)
- [Deployment Scenarios](#deployment-scenarios)
- [Architecture-Specific Considerations](#architecture-specific-considerations)

## Build Architecture

The project uses a **three-layer multi-stage build** to optimize image size and build times:

```
┌─────────────────────────────────────────┐
│  Layer 1: OS (Base System)              │
│  - Python 3.12 Bookworm                 │
│  - System libraries (libgl1, geos, etc) │
│  - pip, uwsgi, uv                       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Layer 2: PIP (Python Dependencies)     │
│  - PyTorch & ML libraries               │
│  - Django & web framework               │
│  - Application dependencies             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  Layer 3: APP (Application Code)        │
│  - Application source code              │
│  - Configuration files                  │
└─────────────────────────────────────────┘
```

### Benefits of Multi-Stage Build

1. **Layer Caching**: OS and PIP layers are rebuilt only when dependencies change
2. **Faster Rebuilds**: Application changes only rebuild the lightweight APP layer
3. **Shared Base**: Multiple deployments can share common base layers
4. **Size Optimization**: Each layer contains only what's necessary

## Multi-Stage Build Process

### Layer 1: OS Base (`docker/images/os/`)

**Purpose**: Provides Python runtime and system-level dependencies

**x86_64 (Dockerfile)**:
```dockerfile
FROM python:3.12-bookworm
RUN apt-get update && apt-get install \
    libgl1 \
    libgeos++-dev \
    libproj-dev \
    libghc-persistent-postgresql-dev \
    -y
RUN pip3 install --upgrade pip
RUN pip3 install uwsgi
RUN pip3 install uv
```

**ARM (Dockerfile.arm)**:
Same as x86_64 - base dependencies are architecture-independent.


### Layer 2: Python Dependencies (`docker/images/pip/`)

**Purpose**: Installs Python packages and ML libraries

**x86_64 (Dockerfile)**:
```dockerfile
FROM protyom/parking-monitoring:os
WORKDIR /app/
COPY pyproject.toml /app/
RUN uv pip install --system --no-cache-dir -e ".[django]" && \
    uv pip install --system --no-cache-dir uwsgi && \
    uv cache clean
```
- Uses standard `django` dependency group
- Supports GPU-enabled PyTorch (if available)
- Suitable for server deployment

**ARM (Dockerfile.arm)**:
```dockerfile
FROM protyom/parking-monitoring:os_arm
WORKDIR /app/
COPY pyproject.toml /app/
RUN uv pip install --system --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    uv pip install --system --no-cache-dir -e ".[orangepi,django]" && \
    uv cache clean
```
- Uses CPU-only PyTorch from special index
- Uses `orangepi` + `django` dependency groups
- Optimized for ARM embedded devices (OrangePi, Raspberry Pi)
- opencv-python-headless instead of full OpenCV


### Layer 3: Application Code (`docker/images/app/`)

**Purpose**: Adds application source code

**x86_64 (Dockerfile)**:
```dockerfile
FROM protyom/parking-monitoring:pip
COPY . /app/
```

**ARM (Dockerfile.arm)**:
```dockerfile
FROM protyom/parking-monitoring:pip_arm
COPY . /app/
```


## Building Images

All images must be built using **Docker Buildx** with explicit platform specification. Standard `docker build` does not support platform selection.

### Prerequisites

1. **Docker Buildx** (included in Docker Desktop 19.03+)

2. **Create buildx builder** (one-time setup):
```bash
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap
```

3. **Enable QEMU** for cross-platform emulation (if building ARM on x86_64):
```bash
docker run --privileged --rm tonistiigi/binfmt --install all
```

### Building x86_64 Images

Build all layers for x86_64/amd64 platform:

#### Layer 1: OS Base
```bash
docker buildx build \
  --platform linux/amd64 \
  -t protyom/parking-monitoring:os \
  -f docker/images/os/Dockerfile \
  --push \
  docker/images/os/
```

To load locally instead of pushing:
```bash
docker buildx build \
  --platform linux/amd64 \
  -t protyom/parking-monitoring:os \
  -f docker/images/os/Dockerfile \
  --load \
  docker/images/os/
```

#### Layer 2: PIP Dependencies
```bash
docker buildx build \
  --platform linux/amd64 \
  -t protyom/parking-monitoring:pip \
  -f docker/images/pip/Dockerfile \
  --push \
  .
```

#### Layer 3: Application
```bash
docker buildx build \
  --platform linux/amd64 \
  -t protyom/parking-monitoring:app \
  -t protyom/parking-monitoring:latest \
  -f docker/images/app/Dockerfile \
  --push \
  .
```

### Building ARM Images

Build all layers for ARM64 platform:

#### Layer 1: OS Base
```bash
docker buildx build \
  --platform linux/arm64 \
  -t protyom/parking-monitoring:os_arm \
  -f docker/images/os/Dockerfile.arm \
  --push \
  docker/images/os/
```

To load locally instead of pushing (on ARM device):
```bash
docker buildx build \
  --platform linux/arm64 \
  -t protyom/parking-monitoring:os_arm \
  -f docker/images/os/Dockerfile.arm \
  --load \
  docker/images/os/
```

#### Layer 2: PIP Dependencies
```bash
docker buildx build \
  --platform linux/arm64 \
  -t protyom/parking-monitoring:pip_arm \
  -f docker/images/pip/Dockerfile.arm \
  --push \
  .
```

#### Layer 3: Application
```bash
docker buildx build \
  --platform linux/arm64 \
  -t protyom/parking-monitoring:app_arm \
  -f docker/images/app/Dockerfile.arm \
  --push \
  .
```

### Automated Build Scripts

**Build all x86_64 images:**

Use the provided `build-x86.sh` script:
```bash
bash build-x86.sh
```

**Build all ARM images:**

Use the provided `build-arm.sh` script:
```bash
bash build-arm.sh
```

These scripts handle all three layers automatically, including builder setup and QEMU installation for ARM cross-compilation.

### Notes

- **`--push` vs `--load`**: Use `--push` to push directly to registry, or `--load` to load into local Docker daemon
- **`--load` limitation**: Can only load one platform at a time
- **Cross-compilation**: ARM builds on x86_64 use QEMU emulation and will be slower (10-30 minutes for PIP layer)
- **Native builds**: Building on native ARM hardware is much faster
- **Platform specification**: Always use `--platform` flag with buildx to ensure correct architecture

## Deployment Scenarios

### 1. Development (Root `docker-compose.yml`)

**Purpose**: Local development and testing

**Location**: Root directory

**Architecture**: x86_64

**Services**:
- `db_postgres`: PostgreSQL database
- `web`: Django development server (port 8080)
- `redis`: Redis broker
- `celerybeat`: Celery scheduler
- `celery`: Celery worker (host network mode)

**Usage**:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

**Environment**: Requires `.env` file with:
```env
APP_IMAGE=protyom/parking-monitoring:app
SECRET_KEY=your-secret-key-here
DEBUG=True
POSTGRES_USER=postgres
POSTGRES_DB=parking
POSTGRES_PASSWORD=secretpassword
POSTGRES_PORT=5432
REDIS_PASSWORD=redispassword
ALLOWED_HOSTS=localhost,127.0.0.1
CAMERA_CONF={"cameras":[...]}
YOLO_PATH=/app/yolov8x.pt
```

### 2. Production Web Server (`deploy/webserver/`)

**Purpose**: Full production deployment with web interface

**Location**: `deploy/webserver/docker-compose.yml`

**Architecture**: x86_64

**Services**:
- `db_postgres`: PostgreSQL database
- `web`: Django app via uWSGI
- `redis`: Redis broker
- `nginx`: Web server serving static files
- `nginx-proxy`: Reverse proxy with SSL termination
- `acme-companion`: Automatic Let's Encrypt SSL certificates

**Features**:
- HTTPS with automatic SSL certificates
- Nginx reverse proxy
- Static file serving
- Production-grade uWSGI server

**Usage**:
```bash
cd deploy/webserver

# Start production stack
docker-compose up -d

# View logs
docker-compose logs -f web nginx

# Stop stack
docker-compose down
```

**Environment**: Requires `.env` in `deploy/webserver/` with production settings.

**Nginx Configuration**: Place nginx config in `configs/nginx/conf.d/app.conf`

### 3. OrangePi/ARM Worker (`deploy/orangepi/`)

**Purpose**: Distributed worker deployment on ARM devices

**Location**: `deploy/orangepi/docker-compose.yml`

**Architecture**: ARM (arm64/aarch64)

**Services**:
- `celerybeat`: Celery scheduler
- `celery`: Celery worker with YOLOv8 inference

**Use Case**: Deploy on ARM devices (OrangePi, Raspberry Pi) connected to cameras for distributed processing.

**Features**:
- Connects to remote PostgreSQL database
- Runs camera monitoring tasks locally
- Uses CPU-optimized PyTorch
- Host network mode for camera access

**Usage**:
```bash
cd deploy/orangepi

# Ensure YOLOv8 model is available
cp /path/to/yolov8x.pt .

# Start worker services
docker-compose up -d

# View logs
docker-compose logs -f celery

# Stop services
docker-compose down
```

**Environment**: Requires `.env` with:
```env
APP_IMAGE=protyom/parking-monitoring:app_arm
SECRET_KEY=your-secret-key-here
DEBUG=False
POSTGRES_HOST=remote-db-host.example.com
POSTGRES_USER=postgres
POSTGRES_DB=parking
POSTGRES_PASSWORD=secretpassword
REDIS_ADDR=remote-redis-host.example.com
REDIS_PASSWORD=redispassword
CAMERA_CONF={"cameras":[...]}
YOLO_PATH=/app/yolov8x.pt
```

**YOLOv8 Model**: Mount model file as volume:
```yaml
volumes:
  - ${PWD}/yolov8x.pt:/app/yolov8x.pt
```

## Architecture-Specific Considerations

### x86_64 (Server Deployment)

**Advantages**:
- Better performance for ML inference
- GPU support available (with CUDA images)
- More memory for larger models
- Suitable for centralized processing

**Recommended Use**:
- Production web servers
- Development environments
- High-traffic deployments
- GPU-accelerated inference

**PyTorch Installation**:
```bash
# Standard PyTorch (may include CUDA support)
uv pip install -e ".[django]"
```

### ARM (OrangePi/Raspberry Pi)

**Advantages**:
- Low power consumption
- Direct camera connection
- Distributed edge processing
- Cost-effective scaling

**Limitations**:
- CPU-only inference (slower)
- Limited memory
- May need model optimization (quantization, pruning)

**Recommended Use**:
- Edge devices near cameras
- Distributed worker nodes
- Low-power deployments
- Cost-sensitive scaling

**PyTorch Installation**:
```bash
# CPU-only PyTorch for ARM
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
uv pip install -e ".[orangepi,django]"
```

**Performance Tips**:
- Use YOLOv8n (nano) or YOLOv8s (small) instead of YOLOv8x for faster inference
- Reduce image resolution before inference
- Increase task interval (e.g., every 5 minutes instead of 2)
- Consider model quantization with TorchScript

## Hybrid Deployment Architecture

For large-scale deployments, combine both architectures:

```
┌─────────────────────────────────────────────────────────────┐
│                    Central Server (x86_64)                   │
│  ┌─────────────┐  ┌──────────┐  ┌───────┐  ┌──────────┐    │
│  │ PostgreSQL  │  │  Redis   │  │ Web   │  │  Nginx   │    │
│  └─────────────┘  └──────────┘  └───────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              │ Network
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Edge Workers (ARM - OrangePi)                   │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ OrangePi #1  │    │ OrangePi #2  │    │ OrangePi #3  │  │
│  │  + Camera 1  │    │  + Camera 2  │    │  + Camera 3  │  │
│  │  + Celery    │    │  + Celery    │    │  + Celery    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Setup**:
1. Deploy webserver stack on x86_64 server
2. Deploy OrangePi workers on edge devices near cameras
3. Configure workers to connect to central database and Redis
4. Each worker processes its local camera feeds
5. Results aggregated in central database
6. Web interface served from central server

## Troubleshooting

### Build Issues

**"Cannot find pyproject.toml"**:
- Build PIP and APP layers from project root, not docker/images directory
- Ensure you're in the correct directory: `cd /path/to/parking_services`

**ARM build fails on x86_64**:
- Use Docker buildx for cross-platform builds
- Or build directly on ARM device

**PyTorch installation timeout on ARM**:
- ARM builds are slower due to CPU-only builds
- Increase Docker build timeout
- Consider pre-building on ARM device and pushing to registry

### Runtime Issues

**OrangePi worker cannot connect to database**:
- Verify `POSTGRES_HOST` is accessible from OrangePi network
- Check firewall rules on database server
- Test connection: `psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB`

**Camera connection fails**:
- OrangePi worker uses `network_mode: host` for camera access
- Verify camera URLs are accessible from the device
- Test with: `ffmpeg -i rtsp://camera-url -frames:v 1 test.jpg`

**Slow inference on ARM**:
- Use smaller YOLO model (yolov8n.pt or yolov8s.pt)
- Reduce image resolution
- Increase task interval
- Consider model optimization/quantization

## Performance Benchmarks

Approximate inference times (single frame):

| Device        | Model    | Resolution | Time    |
|---------------|----------|------------|---------|
| x86_64 (CPU)  | YOLOv8x  | 1920x1080  | ~2s     |
| x86_64 (GPU)  | YOLOv8x  | 1920x1080  | ~0.3s   |
| OrangePi 5    | YOLOv8x  | 1920x1080  | ~15s    |
| OrangePi 5    | YOLOv8n  | 1920x1080  | ~3s     |
| OrangePi 5    | YOLOv8n  | 1280x720   | ~1.5s   |

*Times are approximate and vary based on hardware specs*

## Additional Resources

- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Buildx Documentation](https://docs.docker.com/buildx/working-with-buildx/)
- [PyTorch ARM Installation](https://pytorch.org/get-started/locally/)
- [Ultralytics YOLOv8 Documentation](https://docs.ultralytics.com/)
