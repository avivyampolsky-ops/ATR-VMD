#!/bin/bash
set -e

IMAGE_NAME="atr-vmd-jetson"

echo "=== Building Docker Image for Jetson Orin (JetPack 6.2.1) ==="
# Use host network to avoid DNS issues during build (apt-get update failures)
docker build --network=host -t $IMAGE_NAME .

echo "=== Build Complete ==="
echo "You can now run the container with:"
echo "  docker run --runtime nvidia -it --rm --network host -v \$(pwd):/app $IMAGE_NAME /bin/bash"
echo ""
echo "Or simply run this script with 'run' argument:"
echo "  ./install.sh run"

if [ "$1" == "run" ]; then
    echo "=== Running Container ==="
    docker run --runtime nvidia -it --rm --network host -v $(pwd):/app $IMAGE_NAME /bin/bash
fi
