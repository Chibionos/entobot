import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/device_credentials.dart';
import 'constants.dart';

/// Secure storage wrapper for managing device credentials
class SecureStorageService {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
  );

  /// Save device credentials
  static Future<void> saveCredentials(DeviceCredentials credentials) async {
    await _storage.write(
      key: AppConstants.keyJwtToken,
      value: credentials.jwtToken,
    );
    await _storage.write(
      key: AppConstants.keyDeviceId,
      value: credentials.deviceId,
    );
    await _storage.write(
      key: AppConstants.keyWebsocketUrl,
      value: credentials.websocketUrl,
    );
    await _storage.write(
      key: AppConstants.keyPairedAt,
      value: credentials.pairedAt.toIso8601String(),
    );
  }

  /// Load device credentials
  static Future<DeviceCredentials?> loadCredentials() async {
    try {
      final jwtToken = await _storage.read(key: AppConstants.keyJwtToken);
      final deviceId = await _storage.read(key: AppConstants.keyDeviceId);
      final websocketUrl =
          await _storage.read(key: AppConstants.keyWebsocketUrl);
      final pairedAtStr = await _storage.read(key: AppConstants.keyPairedAt);

      if (jwtToken == null ||
          deviceId == null ||
          websocketUrl == null ||
          pairedAtStr == null) {
        return null;
      }

      return DeviceCredentials(
        jwtToken: jwtToken,
        deviceId: deviceId,
        websocketUrl: websocketUrl,
        pairedAt: DateTime.parse(pairedAtStr),
      );
    } catch (e) {
      // Error reading credentials
      return null;
    }
  }

  /// Clear all credentials
  static Future<void> clearCredentials() async {
    await _storage.delete(key: AppConstants.keyJwtToken);
    await _storage.delete(key: AppConstants.keyDeviceId);
    await _storage.delete(key: AppConstants.keyWebsocketUrl);
    await _storage.delete(key: AppConstants.keyPairedAt);
  }

  /// Check if credentials exist
  static Future<bool> hasCredentials() async {
    final jwtToken = await _storage.read(key: AppConstants.keyJwtToken);
    return jwtToken != null;
  }

  /// Update JWT token (for token refresh)
  static Future<void> updateToken(String newToken) async {
    await _storage.write(
      key: AppConstants.keyJwtToken,
      value: newToken,
    );
  }
}
