#!/bin/bash

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Docker not Found. Please install Docker and retry again."
    exit 1
fi

# Create Temporary directory
temp_dir=$(mktemp -d)

cd $temp_dir

curl -O https://raw.githubusercontent.com/username/repositoryname/main/Dockerfile
curl -O https://raw.githubusercontent.com/username/repositoryname/main/main.py
curl -O https://raw.githubusercontent.com/username/repositoryname/main/requirements.txt
curl -O https://raw.githubusercontent.com/username/repositoryname/main/VERSION

if [ ! -f Dockerfile ]; then
    echo "Dockerfile not found."
    exit 1
fi

if [ ! -f main.py ]; then
    echo "main.py not found."
    exit 1
fi

if [ ! -f requirements.txt ]; then
    echo "requirements.txt not found."
    exit 1
fi

if [ ! -f VERSION ]; then
    echo "VERSION File not found."
    exit 1
fi

# Get latest Version from the VERSION file
version=$(cat VERSION)

# Create Docker image
docker build -t solarplant:$version .

# Check if Image was created successfully
if [ $? -eq 0 ]; then
    echo "Docker-Image 'solarplant:$version' successfully created."
else
    echo "Error while creating a Docker-Image."
    exit 1
fi
rm -rf $temp_dir

echo "Visit Documentation: https://github.com/zumbsy/solarplant"