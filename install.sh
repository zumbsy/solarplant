#!/bin/bash

#
# This Script downloads a python script and creates a Docker Image
# Repo: https://github.com/zumbsy/solarplant
# 
#

# Check if Docker is installed
echo "Checking if Docker is installed"
if ! [ -x "$(command -v docker)" ]; then
    echo "Docker not found"
    exit 1
fi

# Create Temporary directory
echo "Create Temp Directory"
temp_dir=$(mktemp -d)
cd "$temp_dir" || exit

# Download necessary files from GitHub repository
repo_url="https://raw.githubusercontent.com/zumbsy/solarplant/main"
files=(dockerfile main.py requirements.txt VERSION)

echo "Downloading necessary files for the image"
for file in "${files[@]}"
do
    echo "Downloading: $repo_url/$file"
    curl -SfO "$repo_url/$file"
    if [ ! -f "$file" ]; then
        echo "$file not found."
        exit 1
    fi
done

echo "All necessary files downloaded successfully."


# Get latest version from the VERSION file
version=$(cat VERSION)
echo "Latest version: $version"

# Check if image already exists
if [ -n "$(docker images -q solarplant:"$version" 2> /dev/null)" ]; then
  echo "Image 'solarplant:$version' already exists."
  exit 1
fi

# Build Docker image using docker
echo "Building Docker Image"
docker build -t solarplant:"$version" .

# Check if image was created successfully
if [ $? -eq 0 ]; then
    echo "Docker image 'solarplant:$version' successfully created."
else
    echo "Error while creating the Docker image."
    exit 1
fi

# Clean up temporary directory
echo "Cleanup Temp Directory"
rm -rf "$temp_dir"

echo "Visit Documentation: https://github.com/zumbsy/solarplant"
