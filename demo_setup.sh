#!/bin/bash
# Entobot Enterprise Demo Setup Script
# Automated environment preparation for demos

set -e

echo "=================================="
echo "  Entobot Enterprise Demo Setup   "
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "start_server.py" ]; then
    print_error "Error: Must run from entobot root directory"
    exit 1
fi

print_status "Running from correct directory"

# Step 1: Check Python version
echo ""
echo "Step 1: Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_status "Python version: $PYTHON_VERSION"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
    print_error "Python 3.11+ required. Please upgrade Python."
    exit 1
fi

# Step 2: Check dependencies
echo ""
echo "Step 2: Checking dependencies..."

DEPS=("websockets" "fastapi" "qrcode" "PyJWT" "uvicorn" "pillow")
MISSING_DEPS=()

for dep in "${DEPS[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        print_status "$dep installed"
    else
        MISSING_DEPS+=("$dep")
        print_warning "$dep not found"
    fi
done

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo ""
    print_warning "Installing missing dependencies..."
    pip install -e . || {
        print_error "Failed to install dependencies"
        exit 1
    }
    print_status "Dependencies installed"
fi

# Step 3: Check configuration
echo ""
echo "Step 3: Checking configuration..."

CONFIG_FILE="$HOME/.nanobot/config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    print_warning "Configuration not found. Running nanobot onboard..."
    nanobot onboard || {
        print_error "Configuration setup failed"
        exit 1
    }
    print_status "Configuration created"
else
    print_status "Configuration file exists"
fi

# Check for API key
if grep -q '"api_key": "YOUR_API_KEY_HERE"' "$CONFIG_FILE" 2>/dev/null; then
    print_error "API key not configured in $CONFIG_FILE"
    print_warning "Please edit ~/.nanobot/config.json and add your API key"
    exit 1
fi

print_status "API key configured"

# Check for JWT secret
if grep -q '"jwt_secret": "YOUR_STRONG_SECRET"' "$CONFIG_FILE" 2>/dev/null; then
    print_warning "JWT secret not set. Generating one..."
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    echo ""
    echo "Generated JWT secret: $JWT_SECRET"
    print_warning "Please add this to ~/.nanobot/config.json in auth.jwt_secret"
else
    print_status "JWT secret configured"
fi

# Step 4: Check ports availability
echo ""
echo "Step 4: Checking port availability..."

check_port() {
    if nc -z localhost $1 2>/dev/null; then
        return 1  # Port in use
    else
        return 0  # Port available
    fi
}

PORTS=(18790 18791 8080)
PORT_ISSUES=0

for port in "${PORTS[@]}"; do
    if check_port $port; then
        print_status "Port $port available"
    else
        print_error "Port $port already in use"
        PORT_ISSUES=1
    fi
done

if [ $PORT_ISSUES -eq 1 ]; then
    print_warning "Some ports are in use. Kill processes or use different ports."
fi

# Step 5: Create necessary directories
echo ""
echo "Step 5: Creating directories..."

mkdir -p "$HOME/.nanobot/workspace"
mkdir -p "$HOME/.nanobot/logs"

print_status "Directories created"

# Step 6: Start backend server
echo ""
echo "Step 6: Starting backend server..."

print_status "Starting backend server in background..."
nohup python3 start_server.py > "$HOME/.nanobot/logs/server.log" 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 3

if kill -0 $SERVER_PID 2>/dev/null; then
    print_status "Backend server started (PID: $SERVER_PID)"
else
    print_error "Backend server failed to start. Check logs:"
    echo "  tail -f ~/.nanobot/logs/server.log"
    exit 1
fi

# Step 7: Start dashboard
echo ""
echo "Step 7: Starting dashboard..."

if [ -d "dashboard" ]; then
    print_status "Starting dashboard in background..."
    cd dashboard
    nohup python3 app.py > "$HOME/.nanobot/logs/dashboard.log" 2>&1 &
    DASHBOARD_PID=$!
    cd ..
    
    sleep 2
    
    if kill -0 $DASHBOARD_PID 2>/dev/null; then
        print_status "Dashboard started (PID: $DASHBOARD_PID)"
    else
        print_warning "Dashboard failed to start"
    fi
else
    print_warning "Dashboard directory not found. Skipping dashboard."
fi

# Step 8: Generate QR code
echo ""
echo "Step 8: Generating QR code..."

sleep 2  # Wait for pairing manager to initialize

if nanobot pairing generate-qr --save --output demo_qr.png 2>/dev/null; then
    print_status "QR code generated: demo_qr.png"
    print_status "QR code also displayed in terminal"
else
    print_warning "QR code generation failed. Try manually after server fully starts."
fi

# Step 9: Summary
echo ""
echo "=================================="
echo "  Demo Environment Ready!         "
echo "=================================="
echo ""
print_status "Backend Server: http://localhost:18790 (API)"
print_status "WebSocket Server: ws://localhost:18791"
print_status "Dashboard: http://localhost:8080"
echo ""
print_status "QR Code: demo_qr.png (also shown in terminal)"
echo ""
echo "Next Steps:"
echo "  1. Open dashboard: http://localhost:8080"
echo "  2. Scan QR code with mobile app"
echo "  3. Start chatting!"
echo ""
echo "Logs:"
echo "  Backend: tail -f ~/.nanobot/logs/server.log"
echo "  Dashboard: tail -f ~/.nanobot/logs/dashboard.log"
echo ""
echo "To stop servers:"
echo "  kill $SERVER_PID    # Backend"
if [ ! -z "$DASHBOARD_PID" ]; then
    echo "  kill $DASHBOARD_PID  # Dashboard"
fi
echo ""
print_status "Demo setup complete! Ready for presentation."
echo ""
