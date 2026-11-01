#!/bin/bash
set -e

echo "🌊 Pulling latest updates from GitHub..."
git pull origin main || git pull origin master

echo "🚀 Rebuilding and updating Docker containers..."
sudo docker compose up -d --build

echo "✅ BeatWave updated successfully!"
sudo docker compose ps
