import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/websocket_client.dart';
import 'auth_provider.dart';

/// WebSocket connection state
class WebSocketState {
  final ConnectionState state;
  final String? error;

  const WebSocketState({
    this.state = ConnectionState.disconnected,
    this.error,
  });

  WebSocketState copyWith({
    ConnectionState? state,
    String? error,
  }) {
    return WebSocketState(
      state: state ?? this.state,
      error: error,
    );
  }
}

/// WebSocket state notifier
class WebSocketNotifier extends StateNotifier<WebSocketState> {
  final WebSocketClient _client;

  WebSocketNotifier(this._client) : super(const WebSocketState()) {
    // Listen to connection state changes
    _client.stateStream.listen((connectionState) {
      state = WebSocketState(
        state: connectionState,
        error: connectionState == ConnectionState.error ? _client.error : null,
      );
    });
  }

  /// Get current connection state
  ConnectionState get connectionState => _client.state;

  /// Check if connected
  bool get isConnected => _client.state == ConnectionState.connected;

  /// Send message
  void sendMessage(String content) {
    if (!isConnected) {
      throw Exception('Not connected to server');
    }
    _client.sendMessage(content);
  }

  /// Disconnect
  void disconnect() {
    _client.disconnect();
  }

  @override
  void dispose() {
    _client.dispose();
    super.dispose();
  }
}

/// WebSocket state provider
final websocketStateProvider =
    StateNotifierProvider<WebSocketNotifier, WebSocketState>((ref) {
  final client = ref.watch(websocketClientProvider);
  return WebSocketNotifier(client);
});

/// Stream provider for incoming messages
final messagesStreamProvider = StreamProvider<Map<String, dynamic>>((ref) {
  final client = ref.watch(websocketClientProvider);
  return client.messages;
});
