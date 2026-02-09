/// Device credentials model for storing authentication data
class DeviceCredentials {
  final String jwtToken;
  final String deviceId;
  final String websocketUrl;
  final DateTime pairedAt;

  const DeviceCredentials({
    required this.jwtToken,
    required this.deviceId,
    required this.websocketUrl,
    required this.pairedAt,
  });

  factory DeviceCredentials.fromJson(Map<String, dynamic> json) {
    return DeviceCredentials(
      jwtToken: json['jwt_token'] as String,
      deviceId: json['device_id'] as String,
      websocketUrl: json['websocket_url'] as String,
      pairedAt: DateTime.parse(json['paired_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'jwt_token': jwtToken,
      'device_id': deviceId,
      'websocket_url': websocketUrl,
      'paired_at': pairedAt.toIso8601String(),
    };
  }

  DeviceCredentials copyWith({
    String? jwtToken,
    String? deviceId,
    String? websocketUrl,
    DateTime? pairedAt,
  }) {
    return DeviceCredentials(
      jwtToken: jwtToken ?? this.jwtToken,
      deviceId: deviceId ?? this.deviceId,
      websocketUrl: websocketUrl ?? this.websocketUrl,
      pairedAt: pairedAt ?? this.pairedAt,
    );
  }
}
