# Entobot Dashboard - Quick Start Guide

## 3-Step Launch

### Step 1: Navigate
```bash
cd /home/chibionos/r/entobot/dashboard
```

### Step 2: Run
```bash
python app.py
```

### Step 3: Open Browser
```
http://localhost:8080
```

## You're Done!

The dashboard will open with:
- ✅ Demo mode enabled (works without backend)
- ✅ Real-time updates
- ✅ Sample data showing
- ✅ All features active

## Quick Actions

### Generate QR Code
1. Click "Generate QR Code" button (top right)
2. QR modal opens
3. Scan with mobile app
4. Device pairs automatically

### Toggle Demo Mode
1. Click "Demo: ON" button (top right)
2. Switches between demo/real data
3. Perfect for presentations

### View Help
1. Click "?" button (bottom right)
2. Help modal opens
3. Full feature documentation

### Export Audit Log
1. Go to "Security Audit Log" panel
2. Click download icon
3. Saves as text file

## What You'll See

### Status Cards (Top)
- 📡 **System Status**: Online
- 📱 **Devices**: 2 connected
- 💬 **Sessions**: 3 active
- 📊 **Messages**: 45 total
- ⏱️ **Uptime**: 1h 23m

### Main Panels
- 📋 **Recent Activity**: Live event feed
- 📱 **Connected Devices**: Paired devices list
- 🔒 **Audit Log**: Security events

### Bottom Indicators
- Bottom-left: Connection status
- Bottom-right: Help button

## Demo Script (30 seconds)

```
"This is the Entobot Enterprise Dashboard.

[Point to top] Here you can see system status - 2 devices connected,
processing messages in real-time.

[Click Generate QR] To pair a new device, just click here and scan
the QR code with the mobile app.

[Point to activity] All activity updates live - messages, connections,
everything.

[Point to audit] Complete audit trail for compliance.

And [toggle demo] demo mode for presentations."
```

## Troubleshooting

**Dashboard won't start?**
```bash
# Check if port is in use
lsof -i :8080

# Try different port
python app.py  # Edit app.py to change port
```

**No data showing?**
- Demo mode is on by default
- Click "Demo: ON" to toggle
- Real data requires backend running

**Can't generate QR?**
```bash
# Install qrcode package
pip install qrcode[pil]
```

## Features at a Glance

| Feature | Status | Location |
|---------|--------|----------|
| Real-time monitoring | ✅ | Status cards |
| Device list | ✅ | Right panel |
| Activity feed | ✅ | Left panel |
| Audit log | ✅ | Bottom panel |
| QR generation | ✅ | Header button |
| Demo mode | ✅ | Header button |
| WebSocket updates | ✅ | Automatic |
| Export audit | ✅ | Audit panel |
| Help | ✅ | Bottom-right |
| Responsive design | ✅ | All screens |

## URLs

- **Dashboard**: http://localhost:8080
- **Status API**: http://localhost:8080/api/dashboard/status
- **Devices API**: http://localhost:8080/api/dashboard/devices
- **Activity API**: http://localhost:8080/api/dashboard/activity
- **Audit API**: http://localhost:8080/api/dashboard/audit

## Need More Info?

Read the full documentation:
```bash
cat /home/chibionos/r/entobot/dashboard/README.md
```

---

**Ready for Demo!** 🎉
