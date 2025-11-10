#!/bin/bash
set -e

echo "================================================"
echo "Building ARM64 images"
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

# Enable QEMU for cross-platform emulation (if building on x86_64)
echo "Enabling QEMU for cross-platform emulation..."
docker run --privileged --rm tonistiigi/binfmt --install all

echo ""
echo "================================================"
echo "Layer 1: OS Base"
echo "================================================"
docker buildx build \
  --platform linux/arm64 \
  -t protyom/parking-monitoring:os_arm \
  -f docker/images/os/Dockerfile.arm \
  --push \
  docker/images/os/

echo ""
echo "================================================"
echo "Layer 2: PIP Dependencies (may take 10-30 min)"
echo "================================================"
docker buildx build \
  --platform linux/arm64 \
  -t protyom/parking-monitoring:pip_arm \
  -f docker/images/pip/Dockerfile.arm \
  --push \
  .

echo ""
echo "================================================"
echo "Layer 3: Application"
echo "================================================"
docker buildx build \
  --platform linux/arm64 \
  -t protyom/parking-monitoring:app_arm \
  -f docker/images/app/Dockerfile.arm \
  --push \
  .

echo ""
echo "================================================"
echo "✓ ARM64 images built and pushed successfully!"
echo "================================================"
echo ""
echo "Images created:"
echo "  - protyom/parking-monitoring:os_arm (arm64)"
echo "  - protyom/parking-monitoring:pip_arm (arm64)"
echo "  - protyom/parking-monitoring:app_arm (arm64)"
echo ""
