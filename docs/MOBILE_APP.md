# Entobot Enterprise Mobile App User Guide

## Welcome to Entobot Enterprise Mobile

Your secure, enterprise-grade AI assistant - now in your pocket.

---

## Key Features

### 1. Secure QR Code Pairing
- Scan QR code from dashboard
- Instant pairing (< 3 seconds)
- No username or password needed
- Secure JWT authentication

### 2. Real-Time AI Chat
- Ask questions naturally
- Get instant AI responses
- Typing indicators
- Message history

### 3. Mobile Settings
- Configure AI model
- Adjust temperature
- Set response length
- Save preferences

### 4. Offline Support
- Messages queue when offline
- Auto-reconnect
- Seamless experience

---

## Getting Started

### Installation

**For iOS:**
1. Download from App Store (coming soon)
2. Or use TestFlight beta link

**For Android:**
1. Download from Google Play (coming soon)
2. Or install APK directly

**For Development:**
```bash
cd mobile/entobot_flutter
flutter run
```

### First-Time Setup

**Step 1: Open the app**
- Launch Entobot Enterprise
- You'll see the welcome screen

**Step 2: Get QR code**
- Ask your IT administrator for QR code
- Or open dashboard at http://your-company-server.com:8080
- Click "Generate QR Code"

**Step 3: Scan QR code**
- In the app, tap "Scan QR Code"
- Allow camera permissions
- Point camera at QR code on screen
- Wait for "Pairing Successful" message

**Step 4: Start chatting**
- You're ready to go!
- Ask your first question

---

## Using the Chat Interface

### Sending Messages

**Text Message:**
1. Tap the message input field
2. Type your question or message
3. Tap send button (or press Enter)
4. Watch for typing indicator
5. AI response appears in chat

**Example Questions:**
- "What is 2+2?"
- "Explain quantum computing"
- "Write a Python function to sort a list"
- "Summarize the quarterly report"

### Message Features

**Typing Indicators:**
- See "..." when AI is thinking
- Shows processing in real-time

**Message History:**
- Scroll up to see previous messages
- Context maintained in conversation

**Copy Messages:**
- Long-press message to copy
- Paste into other apps

---

## Settings & Configuration

### Accessing Settings

1. Tap the Settings tab (bottom navigation)
2. Or tap menu icon (top-right)
3. Select "Settings"

### Bot Configuration

**AI Model Selection:**
- GPT-4, GPT-4o, GPT-3.5 Turbo
- Claude Opus, Sonnet, Haiku
- And more (depends on your server config)

**Temperature:**
- 0.0 = Precise, consistent responses
- 0.5 = Balanced
- 1.0 = Creative, varied responses

**Max Tokens:**
- 500 = Short responses
- 2000 = Medium responses
- 4000 = Long, detailed responses

**Saving Changes:**
- Tap "Save" button
- Success message confirms
- Changes take effect immediately

### App Settings

**Theme:**
- Light mode
- Dark mode (default)
- System default

**Notifications:**
- Enable/disable (coming soon)
- Sound alerts
- Vibration

**Privacy:**
- Clear message history
- Logout and unpair

---

## Troubleshooting

### Can't Scan QR Code

**Issue:** QR code won't scan

**Solutions:**
1. Ensure good lighting
2. Hold phone steady
3. Keep QR code in focus
4. Increase screen brightness
5. Try manual pairing (if available)

### Connection Issues

**Issue:** "Connection failed" or "Disconnected"

**Solutions:**
1. Check Wi-Fi/mobile data
2. Verify server is running
3. Check firewall settings
4. Re-pair if needed

### Messages Not Sending

**Issue:** Messages stuck or not delivered

**Solutions:**
1. Check internet connection
2. Verify app is not paused/backgrounded
3. Restart app
4. Re-pair device

### Settings Won't Save

**Issue:** Changes to settings don't persist

**Solutions:**
1. Ensure you tapped "Save"
2. Check network connection
3. Verify permissions
4. Contact IT if persists

---

## Privacy & Security

### What Data is Stored?

**On Device:**
- JWT authentication token (encrypted)
- Message history (encrypted)
- App settings (local only)

**On Server:**
- Messages and responses (for context)
- Audit logs (compliance)
- Device metadata (for management)

**NOT Stored:**
- Personal passwords
- Third-party credentials
- Payment information

### Data Security

**In Transit:**
- TLS/SSL encryption
- WebSocket Secure (WSS)
- No plain-text transmission

**At Rest:**
- Encrypted local storage
- Secure keychain (iOS)
- Encrypted preferences (Android)

**On Server:**
- Your enterprise infrastructure
- Your security policies
- Your data retention rules

### Privacy Controls

**You Control:**
- Message history
- Account data
- Pairing/unpairing

**Admin Controls:**
- Access permissions
- Audit logging
- Data retention

---

## Best Practices

### For Best Experience

**Ask Clear Questions:**
- Be specific
- Provide context
- Break complex questions into parts

**Use Appropriate Models:**
- GPT-4o for most tasks (fast + smart)
- GPT-4 for complex reasoning
- GPT-3.5 for simple questions (cheaper)

**Manage Settings:**
- Lower temperature for factual answers
- Higher temperature for creative tasks
- Adjust max tokens based on need

**Security:**
- Don't share authentication tokens
- Log out on shared devices
- Report suspicious activity

---

## App Store Submission Notes

**For iOS App Store:**
- Privacy policy: [Link to privacy policy]
- Terms of service: [Link to terms]
- Support URL: enterprise@entobot.ai
- Category: Business / Productivity
- Age rating: 4+ (or 17+ if LLM allows sensitive content)

**For Google Play:**
- Privacy policy: [Required URL]
- Data safety: See privacy section above
- Content rating: Everyone (or appropriate)
- Category: Business

**Current Status:** Pre-release (demo ready)

---

## Support

### Getting Help

**In-App Support:**
- Tap Settings → Help
- View FAQs
- Contact support

**Email Support:**
- enterprise@entobot.ai
- Include: App version, device model, issue description

**Enterprise IT:**
- Contact your IT administrator
- They manage server and policies

### Reporting Bugs

**How to Report:**
1. Note the issue details
2. Take screenshot if possible
3. Email: support@entobot.ai
4. Include:
   - Device model
   - OS version
   - App version
   - Steps to reproduce

---

## Frequently Asked Questions

**Q: How do I get a QR code?**  
A: Ask your IT administrator or access your company's Entobot dashboard.

**Q: Can I use multiple devices?**  
A: Yes! Scan a new QR code on each device. Each gets its own secure token.

**Q: How long does my session last?**  
A: JWT tokens typically last 24 hours, then auto-refresh. You stay logged in.

**Q: Does this work offline?**  
A: Messages queue offline and send when connection restored.

**Q: Can I delete my messages?**  
A: Message history can be cleared in Settings. Server logs depend on admin policy.

**Q: What AI models are available?**  
A: Depends on your company's server configuration. Check Settings → Bot Configuration.

**Q: Is my data secure?**  
A: Yes. All communication encrypted. Data stays in your company's infrastructure.

**Q: How do I log out?**  
A: Settings → Logout. This unpairs your device.

---

## Screenshots Guide

### Main Screens

**1. Pairing Screen**
- QR code scanner
- Manual pairing option
- Help text

**2. Chat Screen**
- Message list
- Input field
- Send button
- Typing indicator

**3. Settings Screen**
- Bot configuration
- App settings
- About section
- Logout button

**4. Bot Configuration**
- Model selector
- Temperature slider
- Max tokens input
- Save button

---

## Updates & Changelog

**v1.0 (Current - Demo Ready)**
- ✅ QR code pairing
- ✅ Real-time chat
- ✅ Settings management
- ✅ Offline queue
- ✅ Auto-reconnect

**v1.1 (Planned)**
- [ ] Push notifications
- [ ] Voice input
- [ ] File attachments
- [ ] Multi-language

**v2.0 (Future)**
- [ ] Group chats
- [ ] Advanced RAG
- [ ] Custom workflows
- [ ] Plugins

---

## Technical Requirements

**iOS:**
- iOS 13.0 or later
- iPhone 6s or newer
- Camera (for QR scanning)
- Internet connection

**Android:**
- Android 6.0 (API 23) or later
- Camera permission
- Storage permission
- Internet connection

**Network:**
- Wi-Fi or mobile data
- Access to company server (VPN if required)
- Ports: 18790 (API), 18791 (WebSocket)

---

**Thank you for using Entobot Enterprise!**

Your secure AI assistant, always with you.
