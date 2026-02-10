# Pre-Demo Checklist

## 1 Hour Before Demo

### Infrastructure Setup

- [ ] **Backend server tested**
  ```bash
  python start_server.py --verbose
  # Verify: "WebSocket server started on port 18791"
  # Verify: "REST API server started on port 18790"
  ```

- [ ] **Dashboard tested**
  ```bash
  cd dashboard && python app.py
  # Verify: Dashboard accessible at http://localhost:8080
  ```

- [ ] **Verify network connectivity**
  ```bash
  nc -zv localhost 18790  # REST API
  nc -zv localhost 18791  # WebSocket
  nc -zv localhost 8080   # Dashboard
  ```

- [ ] **Test QR code generation**
  ```bash
  nanobot pairing generate-qr
  # Should display QR code in terminal
  ```

- [ ] **Configuration validated**
  ```bash
  cat ~/.nanobot/config.json | grep -E "(api_key|jwt_secret)"
  # Verify: API keys present, JWT secret configured
  ```

### Mobile App Setup

- [ ] **Flutter app installed on device**
- [ ] **Device connected to same network as server**
- [ ] **Camera permissions granted**
- [ ] **Screen brightness set to 100%**
- [ ] **Do Not Disturb enabled**
- [ ] **Test QR scanner works**

### Environment Preparation

- [ ] **Laptop fully charged**
- [ ] **Mobile device fully charged**
- [ ] **Backup device ready (if available)**
- [ ] **Close unnecessary applications**
- [ ] **Disable notifications**
- [ ] **Test screen sharing (if remote demo)**
- [ ] **Prepare large fonts/high contrast for visibility**

### Backup Materials

- [ ] **Screenshots of successful flows**
- [ ] **Pre-generated QR code saved as image**
- [ ] **Demo script open and visible**
- [ ] **Architecture diagram ready**
- [ ] **Slide deck (backup) available**
- [ ] **Pre-recorded demo video (if available)**

### Documentation Ready

- [ ] **DEMO.md script open**
- [ ] **README.md for reference**
- [ ] **QUICKSTART.md for setup questions**
- [ ] **ONE_PAGER.md for executive questions**
- [ ] **EXECUTIVE_SUMMARY.md for business questions**

## 15 Minutes Before Demo

### Final System Checks

- [ ] **Start backend server**
  ```bash
  python start_server.py
  ```

- [ ] **Start dashboard**
  ```bash
  cd dashboard && python app.py
  ```

- [ ] **Open dashboard in browser**
  - Navigate to: http://localhost:8080
  - Verify: Status cards show "Online"

- [ ] **Generate QR code ready**
  ```bash
  nanobot pairing generate-qr --save --output demo_qr.png
  ```

- [ ] **Mobile app opened and ready**

### Presentation Environment

- [ ] **Browser window maximized**
- [ ] **Terminal font size increased (18pt+)**
- [ ] **Screen brightness 100%**
- [ ] **Volume appropriate (if applicable)**
- [ ] **Do Not Disturb enabled**
- [ ] **Hide desktop icons**
- [ ] **Clear browser history/tabs**
- [ ] **Disable auto-lock/screensaver**

### Personal Preparation

- [ ] **Water nearby**
- [ ] **Deep breath - you've got this!**
- [ ] **Review key talking points**
- [ ] **Review Q&A prep**
- [ ] **Smile - show confidence**

## During Demo

### Flow Checklist

- [ ] **Introduction (1 min)**
  - Problem statement
  - Solution overview
  - Key differentiator

- [ ] **Architecture (1 min)**
  - Show diagram
  - Explain components
  - Highlight security

- [ ] **Dashboard Overview (1.5 min)**
  - Status metrics
  - Activity feed
  - Connected devices
  - Audit log

- [ ] **QR Code Pairing (2 min)**
  - Generate QR code
  - Show on screen
  - Scan with mobile app
  - Confirm pairing success

- [ ] **Real-Time Chat (2 min)**
  - Send simple message
  - Show typing indicator
  - Receive AI response
  - Send complex question

- [ ] **Settings Management (1.5 min)**
  - Open settings in app
  - Show bot configuration
  - Change setting
  - Save and confirm

- [ ] **Security & Audit (1 min)**
  - Show audit log
  - Highlight security features
  - Export functionality

- [ ] **Closing (30 sec)**
  - Summarize value
  - Call to action
  - Questions

### Engagement

- [ ] **Speak clearly and slowly**
- [ ] **Make eye contact**
- [ ] **Pause for questions**
- [ ] **Show enthusiasm**
- [ ] **Handle questions professionally**

### Error Handling

- [ ] **Stay calm if something fails**
- [ ] **Use backup plan immediately**
- [ ] **Turn errors into teaching moments**
- [ ] **Never apologize excessively**

## After Demo

### Immediate (Next 30 Minutes)

- [ ] **Thank attendees**
- [ ] **Collect business cards**
- [ ] **Note all questions asked**
- [ ] **Identify next steps**
- [ ] **Schedule follow-up meeting**

### Same Day

- [ ] **Send thank you email**
- [ ] **Share documentation links**
  - QUICKSTART.md
  - ENTERPRISE.md
  - ONE_PAGER.md
  - EXECUTIVE_SUMMARY.md

- [ ] **Send demo recording (if available)**
- [ ] **Propose next steps**
- [ ] **Log feedback**

### Debrief

- [ ] **What went well?**
- [ ] **What could improve?**
- [ ] **What questions came up?**
- [ ] **What surprised you?**
- [ ] **Update demo script with learnings**

## Backup Plan Checklist

### If Backend Fails

- [ ] **Plan A:** Restart server (< 30 seconds)
- [ ] **Plan B:** Enable demo mode in dashboard
- [ ] **Plan C:** Show pre-recorded video
- [ ] **Plan D:** Use slides and screenshots

### If Mobile App Fails

- [ ] **Plan A:** Use wscat (WebSocket CLI)
- [ ] **Plan B:** Use backup device
- [ ] **Plan C:** Show code walkthrough

### If QR Code Won't Scan

- [ ] **Plan A:** Increase brightness and size
- [ ] **Plan B:** Manual entry in app
- [ ] **Plan C:** Use pre-generated QR image

### If Network Fails

- [ ] **Plan A:** Use localhost only
- [ ] **Plan B:** Switch to mobile hotspot
- [ ] **Plan C:** Offline demo mode

### If LLM API Fails

- [ ] **Plan A:** Switch to backup provider
- [ ] **Plan B:** Enable demo responses
- [ ] **Plan C:** Explain architecture instead

## Success Metrics

### Technical Success

- [ ] Server started successfully
- [ ] QR code generated and scanned
- [ ] Mobile app paired
- [ ] Messages sent and received
- [ ] Dashboard showed real-time updates
- [ ] No crashes or critical errors

### Engagement Success

- [ ] Audience asked questions
- [ ] Questions were relevant and technical
- [ ] Positive body language from attendees
- [ ] Note-taking observed
- [ ] Follow-up requested

### Business Success

- [ ] Decision makers present
- [ ] Budget discussion initiated
- [ ] Timeline discussed
- [ ] Next meeting scheduled
- [ ] Technical contact identified
- [ ] Champion identified in audience

## Final Reminders

**You know this system inside and out.**  
**You've tested it multiple times.**  
**It works.**  
**You've got backup plans.**  
**You're prepared.**

**Breathe. Smile. Deliver.**

**Good luck! 🚀**
