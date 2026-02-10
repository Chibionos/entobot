/// QR code pairing data model
class PairingData {
  final String sessionId;
  final String websocketUrl;
  final String tempToken;
  final int timestamp;

  const PairingData({
    required this.sessionId,
    required this.websocketUrl,
    required this.tempToken,
    required this.timestamp,
  });

  factory PairingData.fromJson(Map<String, dynamic> json) {
    return PairingData(
      sessionId: json['session_id'] as String,
      websocketUrl: json['websocket_url'] as String,
      tempToken: json['temp_token'] as String,
      timestamp: json['timestamp'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'session_id': sessionId,
      'websocket_url': websocketUrl,
      'temp_token': tempToken,
      'timestamp': timestamp,
    };
  }

  bool isExpired() {
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    // Consider expired if older than 5 minutes
    return (now - timestamp) > 300;
  }
}
