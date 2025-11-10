#!/bin/bash
set -e

echo "================================================"
echo "Building x86_64 (amd64) images"
echo "================================================"
echo ""

# Ensure buildx builder exists
if ! docker buildx inspect multiarch &>/dev/null; then
    echo "Creating buildx builder 'multiarch'..."
    docker buildx create --name multiarch --use
    docker buildx inspect --bootstrap
else
    echo "Using existing buildx builder 'multiarch'..."
    docker buildx use multiarch
fi

echo ""
echo "================================================"
echo "Layer 1: OS Base"
echo "================================================"
docker buildx build \
  --platform linux/amd64 \
  -t protyom/parking-monitoring:os \
  -f docker/images/os/Dockerfile \
  --push \
  docker/images/os/

echo ""
echo "================================================"
echo "Layer 2: PIP Dependencies"
echo "================================================"
docker buildx build \
  --platform linux/amd64 \
  -t protyom/parking-monitoring:pip \
  -f docker/images/pip/Dockerfile \
  --push \
  .

echo ""
echo "================================================"
echo "Layer 3: Application"
echo "================================================"
docker buildx build \
  --platform linux/amd64 \
  -t protyom/parking-monitoring:app \
  -t protyom/parking-monitoring:latest \
  -f docker/images/app/Dockerfile \
  --push \
  .

echo ""
echo "================================================"
echo "✓ x86_64 images built and pushed successfully!"
echo "================================================"
echo ""
echo "Images created:"
echo "  - protyom/parking-monitoring:os (amd64)"
echo "  - protyom/parking-monitoring:pip (amd64)"
echo "  - protyom/parking-monitoring:app (amd64)"
echo "  - protyom/parking-monitoring:latest (amd64)"
echo ""
