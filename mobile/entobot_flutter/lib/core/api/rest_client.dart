import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/bot_config.dart';
import '../utils/constants.dart';

/// REST API client for configuration and management
class RestClient {
  final String baseUrl;
  String? _jwtToken;

  RestClient({
    this.baseUrl = AppConstants.defaultApiUrl,
    String? jwtToken,
  }) : _jwtToken = jwtToken;

  /// Set JWT token for authenticated requests
  void setToken(String token) {
    _jwtToken = token;
  }

  /// Clear JWT token
  void clearToken() {
    _jwtToken = null;
  }

  /// Get bot configuration
  Future<BotConfig> getBotConfig() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/config'),
        headers: _buildHeaders(),
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        return BotConfig.fromJson(json);
      } else if (response.statusCode == 401) {
        throw Exception('Unauthorized - please re-authenticate');
      } else {
        throw Exception('Failed to get config: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get config: $e');
    }
  }

  /// Update bot configuration
  Future<bool> updateBotConfig(BotConfig config) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/config'),
        headers: _buildHeaders(),
        body: jsonEncode(config.toJson()),
      );

      if (response.statusCode == 200) {
        return true;
      } else if (response.statusCode == 401) {
        throw Exception('Unauthorized - please re-authenticate');
      } else {
        throw Exception('Failed to update config: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to update config: $e');
    }
  }

  /// Get available providers and models
  Future<List<Provider>> getProviders() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/providers'),
        headers: _buildHeaders(),
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        final providers = json['providers'] as List<dynamic>;
        return providers
            .map((p) => Provider.fromJson(p as Map<String, dynamic>))
            .toList();
      } else if (response.statusCode == 401) {
        throw Exception('Unauthorized - please re-authenticate');
      } else {
        throw Exception('Failed to get providers: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get providers: $e');
    }
  }

  /// Refresh JWT token
  Future<String> refreshToken(String oldToken) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/refresh'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $oldToken',
        },
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        final newToken = json['jwt_token'] as String;
        _jwtToken = newToken;
        return newToken;
      } else {
        throw Exception('Failed to refresh token: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to refresh token: $e');
    }
  }

  /// Get paired devices
  Future<List<Device>> getDevices() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/devices'),
        headers: _buildHeaders(),
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body) as Map<String, dynamic>;
        final devices = json['devices'] as List<dynamic>;
        return devices
            .map((d) => Device.fromJson(d as Map<String, dynamic>))
            .toList();
      } else if (response.statusCode == 401) {
        throw Exception('Unauthorized - please re-authenticate');
      } else {
        throw Exception('Failed to get devices: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get devices: $e');
    }
  }

  /// Revoke current device token
  Future<bool> revokeToken() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/revoke'),
        headers: _buildHeaders(),
      );

      return response.statusCode == 200;
    } catch (e) {
      throw Exception('Failed to revoke token: $e');
    }
  }

  Map<String, String> _buildHeaders() {
    final headers = <String, String>{
      'Content-Type': 'application/json',
    };

    if (_jwtToken != null) {
      headers['Authorization'] = 'Bearer $_jwtToken';
    }

    return headers;
  }
}

/// Device model
class Device {
  final String deviceId;
  final String deviceInfo;
  final DateTime pairedAt;
  final DateTime lastSeen;

  const Device({
    required this.deviceId,
    required this.deviceInfo,
    required this.pairedAt,
    required this.lastSeen,
  });

  factory Device.fromJson(Map<String, dynamic> json) {
    return Device(
      deviceId: json['device_id'] as String,
      deviceInfo: json['device_info'] as String,
      pairedAt: DateTime.parse(json['paired_at'] as String),
      lastSeen: DateTime.parse(json['last_seen'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'device_id': deviceId,
      'device_info': deviceInfo,
      'paired_at': pairedAt.toIso8601String(),
      'last_seen': lastSeen.toIso8601String(),
    };
  }
}
