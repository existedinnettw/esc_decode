#!/bin/bash

# ESC Decode LXC Container Setup Script
# This script sets up an LXC container for the ESC decode Python application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="esc-decode-python"
PROFILE_NAME="esc-decode-python"
UBUNTU_VERSION="24.04"

echo -e "${GREEN}Starting ESC Decode LXC Container Setup${NC}"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run this script as root or with sudo${NC}"
    exit 1
fi

# Check if LXD is installed
if ! command -v lxc &> /dev/null; then
    echo -e "${YELLOW}LXC/LXD not found. Installing...${NC}"
    apt update
    apt install -y lxd lxd-client
    lxd init --auto
fi

# Check if LXD is initialized
if ! lxc info &> /dev/null; then
    echo -e "${YELLOW}Initializing LXD...${NC}"
    lxd init --auto
fi

# Stop and delete existing container if it exists
if lxc info "$CONTAINER_NAME" &> /dev/null; then
    echo -e "${YELLOW}Stopping existing container: $CONTAINER_NAME${NC}"
    lxc stop "$CONTAINER_NAME" --force || true
    echo -e "${YELLOW}Deleting existing container: $CONTAINER_NAME${NC}"
    lxc delete "$CONTAINER_NAME" --force || true
fi

# Delete existing profile if it exists
if lxc profile show "$PROFILE_NAME" &> /dev/null; then
    echo -e "${YELLOW}Deleting existing profile: $PROFILE_NAME${NC}"
    lxc profile delete "$PROFILE_NAME" || true
fi

# Create the profile from the YAML file
echo -e "${GREEN}Creating LXC profile: $PROFILE_NAME${NC}"
lxc profile create "$PROFILE_NAME"
cat lxc-profile.yaml | lxc profile edit "$PROFILE_NAME"

# Launch the container
echo -e "${GREEN}Launching container: $CONTAINER_NAME${NC}"
lxc launch ubuntu:$UBUNTU_VERSION "$CONTAINER_NAME" --profile "$PROFILE_NAME"

# Wait for the container to be ready
echo -e "${YELLOW}Waiting for container to be ready...${NC}"
lxc exec "$CONTAINER_NAME" -- cloud-init status --wait

# Copy the project files to the container
echo -e "${GREEN}Copying project files to container...${NC}"
lxc file push -r esc_decode/ "$CONTAINER_NAME"/app/
lxc file push pyproject.toml "$CONTAINER_NAME"/app/
lxc file push README.md "$CONTAINER_NAME"/app/

# Install project dependencies if pyproject.toml exists
if [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}Installing project dependencies...${NC}"
    lxc exec "$CONTAINER_NAME" -- bash -c "cd /app && source /app/venv/bin/activate && pip install -e ."
fi

# Set executable permissions for Python files
echo -e "${GREEN}Setting permissions...${NC}"
lxc exec "$CONTAINER_NAME" -- chmod +x /app/esc_decode/__main__.py

# Test the installation
echo -e "${GREEN}Testing the installation...${NC}"
lxc exec "$CONTAINER_NAME" -- bash -c "cd /app && source /app/venv/bin/activate && python -c 'import esc_decode; print(\"ESC Decode module imported successfully!\")'"

echo -e "${GREEN}Container setup complete!${NC}"
echo -e "${YELLOW}To access the container:${NC}"
echo -e "  lxc exec $CONTAINER_NAME -- bash"
echo -e "${YELLOW}To run the ESC decode application:${NC}"
echo -e "  lxc exec $CONTAINER_NAME -- bash -c 'cd /app && source /app/venv/bin/activate && python -m esc_decode'"
echo -e "${YELLOW}To stop the container:${NC}"
echo -e "  lxc stop $CONTAINER_NAME"
echo -e "${YELLOW}To start the container:${NC}"
echo -e "  lxc start $CONTAINER_NAME"