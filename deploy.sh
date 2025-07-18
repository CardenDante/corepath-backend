#!/bin/bash

# CorePath Impact Backend Deployment Script
# This script deploys the FastAPI backend using Docker

set -e

echo "🚀 Starting CorePath Impact Backend Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="corepath-backend"
DOMAIN="api.chach-a.com"
EMAIL="cardendante@gmail.com"  # Change this to your email

# Check if running as root and warn (but allow)
if [[ $EUID -eq 0 ]]; then
   echo -e "${YELLOW}Warning: Running as root. Consider creating a non-root user for better security.${NC}"
   echo -e "${YELLOW}Continuing in 5 seconds... (Ctrl+C to cancel)${NC}"
   sleep 5
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Function to generate random secret key
generate_secret_key() {
    openssl rand -hex 32
}

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOF
# CorePath Impact Backend Environment Variables
SECRET_KEY=$(generate_secret_key)
DEBUG=false
PROJECT_NAME=CorePath Impact API
VERSION=1.0.0
API_V1_STR=/api/v1

# Database
DATABASE_URL=sqlite:///./corepath.db

# Security
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
ALLOWED_IMAGE_TYPES=jpg,jpeg,png,gif,webp

# Email Configuration (Optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
FROM_EMAIL=noreply@corepathimpact.com

# Stripe Configuration (Optional)
STRIPE_PUBLISHABLE_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# WordPress Integration (Optional)
WORDPRESS_API_URL=

# Points and Rewards
REFERRAL_POINTS=500
SIGNUP_BONUS_POINTS=100
ORDER_POINTS_RATE=0.01
EOF
    echo -e "${GREEN}Created .env file. Please edit it with your configuration.${NC}"
else
    echo -e "${GREEN}Using existing .env file.${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p uploads/{products,users,courses}
mkdir -p static
mkdir -p ssl

# Build and start the application
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose build

echo -e "${YELLOW}Starting the application...${NC}"
docker-compose up -d

# Wait for the application to start
echo -e "${YELLOW}Waiting for application to start...${NC}"
sleep 10

# Check if the application is running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Application is running successfully!${NC}"
else
    echo -e "${RED}❌ Application failed to start. Check logs with: docker-compose logs${NC}"
    exit 1
fi

# Install Certbot for SSL certificates
echo -e "${YELLOW}Setting up SSL certificates...${NC}"
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Installing Certbot...${NC}"
    apt-get update
    apt-get install -y certbot
fi

# Generate SSL certificate
echo -e "${YELLOW}Generating SSL certificate for $DOMAIN...${NC}"
if [[ $EUID -eq 0 ]]; then
    certbot certonly --standalone \
        --email $EMAIL \
        --agree-tos \
        --non-interactive \
        --domains $DOMAIN \
        --pre-hook "docker-compose stop nginx" \
        --post-hook "docker-compose start nginx"
else
    sudo certbot certonly --standalone \
        --email $EMAIL \
        --agree-tos \
        --non-interactive \
        --domains $DOMAIN \
        --pre-hook "docker-compose stop nginx" \
        --post-hook "docker-compose start nginx"
fi

# Copy SSL certificates to nginx directory
if [[ $EUID -eq 0 ]]; then
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/
    chmod 644 ssl/*.pem
else
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/
    sudo chown $USER:$USER ssl/*.pem
fi

# Restart nginx with SSL
echo -e "${YELLOW}Restarting nginx with SSL...${NC}"
docker-compose restart nginx

# Setup automatic SSL renewal
echo -e "${YELLOW}Setting up automatic SSL renewal...${NC}"
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --pre-hook 'docker-compose stop nginx' --post-hook 'docker-compose start nginx'") | crontab -

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}Your API is now available at: https://$DOMAIN${NC}"
echo -e "${GREEN}API Documentation: https://$DOMAIN/docs${NC}"
echo -e "${GREEN}Health Check: https://$DOMAIN/health${NC}"

echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Edit .env file with your configuration"
echo "2. Set up your database schema: docker-compose exec app alembic upgrade head"
echo "3. Configure your email settings in .env"
echo "4. Set up Stripe keys for payments"
echo "5. Monitor logs with: docker-compose logs -f"

echo -e "${YELLOW}🛠️ Useful commands:${NC}"
echo "- View logs: docker-compose logs -f"
echo "- Restart app: docker-compose restart"
echo "- Stop app: docker-compose down"
echo "- Update app: git pull && docker-compose build && docker-compose up -d"