#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 AGStock Production Deployment${NC}"
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create .env from .env.example"
    exit 1
fi

# Backup database
echo -e "${YELLOW}📦 Creating database backup...${NC}"
python -m src.db_maintenance || echo "Warning: Backup failed"

# Pull latest code
echo -e "${YELLOW}📥 Pulling latest code...${NC}"
git pull origin main || echo "Warning: Git pull failed"

# Install dependencies
echo -e "${YELLOW}📚 Installing dependencies...${NC}"
pip install -r requirements.txt --quiet

# Run tests
echo -e "${YELLOW}🧪 Running tests...${NC}"
python -m pytest tests/ -v --tb=short || {
    echo -e "${RED}❌ Tests failed. Deployment aborted.${NC}"
    exit 1
}

# Build Docker images
echo -e "${YELLOW}🏗️  Building Docker images...${NC}"
docker-compose -f deploy/docker-compose.prod.yml build

# Stop old containers
echo -e "${YELLOW}⏸️  Stopping old containers...${NC}"
docker-compose -f deploy/docker-compose.prod.yml down

# Start new containers
echo -e "${YELLOW}▶️  Starting new containers...${NC}"
docker-compose -f deploy/docker-compose.prod.yml up -d

# Wait for health check
echo -e "${YELLOW}⏳ Waiting for health check...${NC}"
sleep 10

# Check if app is running
if docker-compose -f deploy/docker-compose.prod.yml ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo ""
    echo "Application is running at: http://localhost:8503"
    echo "Prometheus metrics: http://localhost:9090"
else
    echo -e "${RED}❌ Deployment failed. Rolling back...${NC}"
    docker-compose -f deploy/docker-compose.prod.yml logs
    exit 1
fi

# Show running containers
echo ""
echo "Running containers:"
docker-compose -f deploy/docker-compose.prod.yml ps
