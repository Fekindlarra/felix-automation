#!/bin/bash
set -e

# FASE 15 Quick Setup Script
# Automates the initial validation setup for Track A and Track B

echo "🚀 FASE 15 Quick Setup"
echo "===================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "FASE_15_ARCHITECTURE.md" ]; then
    echo -e "${RED}❌ Error: Not in felix-automation directory${NC}"
    echo "Please run this script from the project root:"
    echo "  cd /home/claude/felix-automation"
    echo "  bash setup-fase15.sh"
    exit 1
fi

echo -e "${YELLOW}Step 1: Checking Python${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

echo ""
echo -e "${YELLOW}Step 2: Checking Node.js${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js $NODE_VERSION${NC}"

echo ""
echo -e "${YELLOW}Step 3: Installing Python dependencies${NC}"
pip install -q -r requirements-fase15.txt
echo -e "${GREEN}✅ Python dependencies installed${NC}"

echo ""
echo -e "${YELLOW}Step 4: Installing React Native dependencies${NC}"
cd frontend/mobile
npm install -q
echo -e "${GREEN}✅ React Native dependencies installed${NC}"
cd ../../

echo ""
echo -e "${YELLOW}Step 5: Creating .env file${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created (using defaults)${NC}"
else
    echo -e "${YELLOW}⚠️  .env already exists, skipping${NC}"
fi

echo ""
echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1️⃣  Start the backend (Track B):"
echo "   cd backend/api"
echo "   python main.py"
echo ""
echo "2️⃣  Start the frontend (Track A) in another terminal:"
echo "   cd frontend/mobile"
echo "   npm start"
echo "   Then press 'i' for iOS or 'a' for Android"
echo ""
echo "3️⃣  Run tests:"
echo "   Backend:  cd backend/api && pytest tests/ -v"
echo "   Frontend: cd frontend/mobile && npm run test:coverage"
echo ""
echo "📋 Full validation checklist:"
echo "   See: FASE_15_VALIDATION_CHECKLIST.md"
echo ""
echo "📚 Architecture documentation:"
echo "   See: FASE_15_ARCHITECTURE.md"
echo ""
