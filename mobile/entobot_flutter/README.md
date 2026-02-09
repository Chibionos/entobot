# Entobot Flutter Mobile App

Enterprise-grade Flutter mobile application for iOS and Android that connects securely to the Entobot AI assistant desktop application.

## Overview

This Flutter app provides a mobile interface to interact with your Entobot desktop AI assistant. It uses QR code pairing for secure authentication and WebSocket communication for real-time chat.

## Features

- **QR Code Pairing**: Secure pairing with desktop app via QR code scanning
- **Real-time Chat**: WebSocket-based instant messaging with AI assistant
- **Secure Authentication**: JWT token-based auth with secure local storage
- **Bot Configuration**: Customize model, temperature, and other parameters
- **Material Design 3**: Modern, professional UI with light/dark theme support
- **Cross-platform**: Works on both iOS and Android devices

## Architecture

### Project Structure

```
lib/
├── main.dart                       # App entry point with routing
├── core/
│   ├── api/
│   │   ├── websocket_client.dart   # WebSocket connection management
│   │   ├── rest_client.dart        # REST API client
│   │   └── auth_service.dart       # Authentication orchestration
│   ├── models/
│   │   ├── message.dart            # Chat message model
│   │   ├── bot_config.dart         # Bot configuration model
│   │   ├── pairing_data.dart       # QR code pairing data
│   │   └── device_credentials.dart # JWT storage model
│   ├── providers/
│   │   ├── auth_provider.dart      # Authentication state (Riverpod)
│   │   ├── websocket_provider.dart # Connection state
│   │   └── messages_provider.dart  # Message history
│   └── utils/
│       ├── secure_storage.dart     # Encrypted credentials storage
│       └── constants.dart          # App constants
├── features/
│   ├── pairing/
│   │   └── qr_scan_screen.dart     # QR code scanner
│   ├── chat/
│   │   ├── chat_screen.dart        # Main chat interface
│   │   └── widgets/                # Chat UI components
│   └── settings/
│       ├── settings_screen.dart    # Main settings
│       ├── bot_config_screen.dart  # Bot configuration
│       ├── security_screen.dart    # Security settings
│       └── about_screen.dart       # About screen
└── theme/
    └── app_theme.dart              # Material 3 theme
```

### Technology Stack

- **Flutter 3.x** - Cross-platform framework
- **Riverpod** - State management
- **GoRouter** - Navigation
- **WebSocket** - Real-time communication
- **HTTP** - REST API calls
- **flutter_secure_storage** - Encrypted credential storage
- **mobile_scanner** - QR code scanning
- **Material Design 3** - Modern UI design system

## Backend Integration

### WebSocket Communication

**WebSocket URL**: `ws://localhost:18791` (development)

**Connection Flow**:

1. **Pairing (new device)**:
   ```dart
   // Scan QR code to get pairing data
   {
     "session_id": "abc123",
     "websocket_url": "ws://host:port",
     "temp_token": "temp_xyz",
     "timestamp": 1234567890
   }

   // Send pairing message
   {
     "type": "pair",
     "session_id": "...",
     "temp_token": "...",
     "device_info": "..."
   }

   // Receive auth success
   {
     "type": "auth_success",
     "jwt_token": "...",
     "device_id": "..."
   }
   ```

2. **Authentication (returning device)**:
   ```dart
   // Send auth message with saved JWT
   {
     "type": "auth",
     "jwt_token": "..."
   }

   // Receive auth success
   {
     "type": "auth_success",
     "device_id": "..."
   }
   ```

3. **Sending Messages**:
   ```dart
   {
     "type": "message",
     "content": "Hello Entobot!"
   }
   ```

4. **Receiving Responses**:
   ```dart
   {
     "type": "message",
     "content": "AI response here..."
   }
   ```

### REST API

**Base URL**: `http://localhost:18790/api/v1`

**Endpoints**:
- `GET /config` - Get bot configuration
- `PUT /config` - Update bot configuration
- `GET /providers` - Get available AI providers
- `GET /devices` - Get paired devices
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/revoke` - Revoke access token

## Getting Started

### Prerequisites

- Flutter SDK 3.0 or higher
- iOS: Xcode 13+ (for iOS development)
- Android: Android Studio with SDK 26+ (Android 8.0+)
- Running Entobot desktop application (backend)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd entobot/mobile/entobot_flutter
   ```

2. **Install dependencies**:
   ```bash
   flutter pub get
   ```

3. **Configure backend URLs** (if not using localhost):
   Edit `lib/core/utils/constants.dart`:
   ```dart
   static const String defaultWsUrl = 'ws://your-server:18791';
   static const String defaultApiUrl = 'http://your-server:18790/api/v1';
   ```

### Running the App

**Development Mode**:
```bash
# iOS
flutter run -d ios

# Android
flutter run -d android

# Or select device interactively
flutter run
```

**Release Mode**:
```bash
# iOS
flutter build ios --release

# Android
flutter build apk --release
# or
flutter build appbundle --release
```

### First-Time Setup

1. Launch the Entobot desktop application
2. Generate a pairing QR code in the desktop app
3. Open the mobile app
4. Grant camera permissions when prompted
5. Scan the QR code
6. Wait for pairing confirmation
7. Start chatting!

## Configuration

### iOS Configuration

**Info.plist** includes:
- Camera permission (`NSCameraUsageDescription`)
- Minimum deployment target: iOS 13.0

**Bundle Identifier**: `com.entobot.entobot_flutter`

### Android Configuration

**AndroidManifest.xml** includes:
- Camera permission
- Internet permission
- Minimum SDK: 26 (Android 8.0)

**Package Name**: `com.entobot.entobot_flutter`

## Security

### Credential Storage

- JWT tokens are stored using `flutter_secure_storage`
- On iOS: Stored in Keychain
- On Android: Encrypted with Android Keystore

### Best Practices

- Never log JWT tokens
- Always use HTTPS/WSS in production
- Validate all QR code data before pairing
- Implement certificate pinning for production
- Regular token refresh to maintain security

## Development

### Code Style

- Follow Flutter/Dart style guide
- Use const constructors where possible
- Proper null safety
- Comprehensive error handling

### State Management

The app uses Riverpod providers:
- `authProvider` - Authentication state
- `websocketStateProvider` - Connection state
- `messagesProvider` - Message history

### Adding New Features

1. Create feature in `lib/features/<feature-name>/`
2. Add models in `lib/core/models/` if needed
3. Create provider in `lib/core/providers/` for state
4. Add routes in `lib/main.dart`
5. Update navigation

## Testing

### Run Analysis

```bash
flutter analyze
```

### Run Tests

```bash
flutter test
```

### Test Coverage

- Unit tests for models and utilities
- Widget tests for UI components
- Integration tests for full flows

## Troubleshooting

### Common Issues

**Camera Permission Denied**:
- Go to Settings > Entobot > Permissions > Camera
- Enable camera access

**Connection Failed**:
- Ensure desktop app is running
- Check firewall settings
- Verify WebSocket URL is correct
- Try regenerating QR code

**Pairing Timeout**:
- QR codes expire after 5 minutes
- Generate a new QR code
- Ensure device has network connectivity

**JWT Token Expired**:
- App will automatically attempt token refresh
- If refresh fails, you'll need to re-pair

## Production Deployment

### iOS App Store

1. Update version in `pubspec.yaml`
2. Build release: `flutter build ios --release`
3. Open Xcode workspace
4. Archive and submit to App Store

### Google Play Store

1. Update version in `pubspec.yaml`
2. Build bundle: `flutter build appbundle --release`
3. Sign the bundle
4. Upload to Google Play Console

### Environment Configuration

For production deployment:
1. Update URLs in `constants.dart` to production servers
2. Enable certificate pinning
3. Configure proper signing certificates
4. Set up CI/CD pipeline

## Known Issues

- QR scanner requires good lighting conditions
- WebSocket reconnection may have delays on poor connections
- Some older Android devices may have performance issues

## Future Enhancements

- Voice input support
- Push notifications for messages
- Multi-language support
- Offline message queue
- Biometric authentication
- Chat history persistence
- Export chat conversations
- Custom theme colors

## License

See main repository license

## Support

For issues and questions, please file issues on the main Entobot repository.

---

**Built with Flutter**
