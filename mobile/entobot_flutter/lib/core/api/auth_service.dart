import '../models/device_credentials.dart';
import '../models/pairing_data.dart';
import '../utils/secure_storage.dart';
import 'websocket_client.dart';
import 'rest_client.dart';

/// Authentication service coordinating auth flow
class AuthService {
  final WebSocketClient wsClient;
  final RestClient restClient;

  AuthService({
    required this.wsClient,
    required this.restClient,
  });

  /// Pair with QR code data
  Future<DeviceCredentials?> pairWithQrCode(PairingData pairingData) async {
    try {
      // Validate pairing data
      if (pairingData.isExpired()) {
        throw Exception('QR code has expired. Please scan a new one.');
      }

      // Connect with pairing data
      final success = await wsClient.connectWithPairing(pairingData);

      if (!success) {
        throw Exception(wsClient.error ?? 'Pairing failed');
      }

      // Wait for auth success message with JWT
      DeviceCredentials? credentials;

      await for (final msg in wsClient.messages) {
        if (msg['type'] == 'auth_success') {
          final jwtToken = msg['jwt_token'] as String?;
          final deviceId = msg['device_id'] as String?;

          if (jwtToken != null && deviceId != null) {
            credentials = DeviceCredentials(
              jwtToken: jwtToken,
              deviceId: deviceId,
              websocketUrl: pairingData.websocketUrl,
              pairedAt: DateTime.now(),
            );

            // Save credentials
            await SecureStorageService.saveCredentials(credentials);

            // Set token for REST client
            restClient.setToken(jwtToken);

            break;
          }
        }
      }

      return credentials;
    } catch (e) {
      rethrow;
    }
  }

  /// Authenticate with saved credentials
  Future<bool> authenticateWithCredentials() async {
    try {
      // Load saved credentials
      final credentials = await SecureStorageService.loadCredentials();

      if (credentials == null) {
        return false;
      }

      // Set token for REST client
      restClient.setToken(credentials.jwtToken);

      // Connect with JWT
      final success = await wsClient.connectWithAuth(
        credentials.websocketUrl,
        credentials.jwtToken,
      );

      return success;
    } catch (e) {
      return false;
    }
  }

  /// Refresh token if expired
  Future<bool> refreshTokenIfNeeded() async {
    try {
      final credentials = await SecureStorageService.loadCredentials();

      if (credentials == null) {
        return false;
      }

      // Try to refresh token
      final newToken = await restClient.refreshToken(credentials.jwtToken);

      // Update stored credentials
      await SecureStorageService.updateToken(newToken);

      // Update REST client
      restClient.setToken(newToken);

      return true;
    } catch (e) {
      return false;
    }
  }

  /// Logout and clear credentials
  Future<void> logout() async {
    try {
      // Try to revoke token on server
      await restClient.revokeToken();
    } catch (e) {
      // Ignore errors, we're logging out anyway
    }

    // Disconnect WebSocket
    wsClient.disconnect();

    // Clear stored credentials
    await SecureStorageService.clearCredentials();

    // Clear REST client token
    restClient.clearToken();
  }

  /// Check if authenticated
  Future<bool> isAuthenticated() async {
    return await SecureStorageService.hasCredentials();
  }

  /// Get current credentials
  Future<DeviceCredentials?> getCredentials() async {
    return await SecureStorageService.loadCredentials();
  }
}
