#!/bin/bash

# Setup script for OKR Performance System

echo "=== OKR Performance System Setup ==="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created. Please edit it with your configuration."
else
    echo "✓ .env file already exists."
fi

echo ""
echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo ""
echo "=== Running database migrations ==="
python manage.py migrate

echo ""
echo "=== Creating superuser ==="
echo "Please enter superuser details:"
python manage.py createsuperuser

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To start the development server, run:"
echo "  python manage.py runserver"
echo ""
echo "Or use Docker:"
echo "  docker-compose up"
echo ""
echo "Access the application at:"
echo "  - API Documentation: http://localhost:8000/swagger/"
echo "  - Django Admin: http://localhost:8000/admin/"
