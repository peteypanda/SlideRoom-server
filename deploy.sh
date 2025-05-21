#!/bin/bash

# Variables - Replace these with your values
DOMAIN="your_domain.com"
APP_PATH="/path/to/your/app"
VENV_PATH="/path/to/your/venv"

# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-venv nginx certbot python3-certbot-nginx

# Create virtual environment and install dependencies
python3 -m venv $VENV_PATH
source $VENV_PATH/bin/activate
pip install -r requirements.txt

# Set up Nginx
sudo cp nginx.conf /etc/nginx/sites-available/$DOMAIN
sudo ln -s /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo sed -i "s|your_domain.com|$DOMAIN|g" /etc/nginx/sites-available/$DOMAIN
sudo sed -i "s|/path/to/your/app|$APP_PATH|g" /etc/nginx/sites-available/$DOMAIN

# Get SSL certificate
sudo certbot --nginx -d $DOMAIN

# Set up Gunicorn service
sudo cp slideroom.service /etc/systemd/system/
sudo sed -i "s|/path/to/your/app|$APP_PATH|g" /etc/systemd/system/slideroom.service
sudo sed -i "s|/path/to/your/venv|$VENV_PATH|g" /etc/systemd/system/slideroom.service

# Start services
sudo systemctl daemon-reload
sudo systemctl start slideroom
sudo systemctl enable slideroom
sudo systemctl restart nginx

echo "Deployment complete! Check the status with:"
echo "sudo systemctl status slideroom"
echo "sudo systemctl status nginx"
