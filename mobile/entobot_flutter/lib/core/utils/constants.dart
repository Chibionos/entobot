/// Application constants
class AppConstants {
  // API Configuration
  static const String defaultWsUrl = 'ws://localhost:18791';
  static const String defaultApiUrl = 'http://localhost:18790/api/v1';

  // Production URLs (update for deployment)
  static const String prodWsUrl = 'wss://your-domain.com:18791';
  static const String prodApiUrl = 'https://your-domain.com:18790/api/v1';

  // Secure Storage Keys
  static const String keyJwtToken = 'jwt_token';
  static const String keyDeviceId = 'device_id';
  static const String keyWebsocketUrl = 'websocket_url';
  static const String keyPairedAt = 'paired_at';

  // Connection Settings
  static const Duration reconnectDelay = Duration(seconds: 2);
  static const Duration maxReconnectDelay = Duration(seconds: 30);
  static const int maxReconnectAttempts = 10;
  static const Duration pingInterval = Duration(seconds: 30);

  // UI Settings
  static const int maxMessageLength = 4000;
  static const int messageInputMaxLines = 5;

  // Device Info
  static String getDeviceInfo() {
    // In production, you'd use device_info_plus package
    return 'Flutter Mobile Client';
  }
}

/// WebSocket message types
class WsMessageType {
  static const String pair = 'pair';
  static const String auth = 'auth';
  static const String authSuccess = 'auth_success';
  static const String authError = 'auth_error';
  static const String message = 'message';
  static const String error = 'error';
  static const String ping = 'ping';
  static const String pong = 'pong';
}
