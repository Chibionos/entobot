import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;
import '../models/pairing_data.dart';
import '../utils/constants.dart';

enum ConnectionState {
  disconnected,
  connecting,
  connected,
  error,
}

/// WebSocket client for managing real-time communication
class WebSocketClient {
  WebSocketChannel? _channel;
  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  final _stateController = StreamController<ConnectionState>.broadcast();

  ConnectionState _state = ConnectionState.disconnected;
  String? _error;
  Timer? _reconnectTimer;
  Timer? _pingTimer;
  int _reconnectAttempts = 0;

  // Getters
  Stream<Map<String, dynamic>> get messages => _messageController.stream;
  Stream<ConnectionState> get stateStream => _stateController.stream;
  ConnectionState get state => _state;
  String? get error => _error;

  /// Connect with JWT authentication
  Future<bool> connectWithAuth(String url, String jwtToken) async {
    try {
      _updateState(ConnectionState.connecting);
      _error = null;

      final uri = Uri.parse(url);
      _channel = WebSocketChannel.connect(uri);

      // Listen to messages
      _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
      );

      // Send auth message
      _sendRaw({
        'type': WsMessageType.auth,
        'jwt_token': jwtToken,
      });

      // Wait for auth success (with timeout)
      final completer = Completer<bool>();
      StreamSubscription? subscription;

      subscription = _messageController.stream.listen((msg) {
        if (msg['type'] == WsMessageType.authSuccess) {
          if (!completer.isCompleted) {
            completer.complete(true);
            subscription?.cancel();
          }
        } else if (msg['type'] == WsMessageType.authError) {
          if (!completer.isCompleted) {
            _error = msg['message'] as String? ?? 'Authentication failed';
            completer.complete(false);
            subscription?.cancel();
          }
        }
      });

      // Timeout after 10 seconds
      Future.delayed(const Duration(seconds: 10), () {
        if (!completer.isCompleted) {
          _error = 'Authentication timeout';
          completer.complete(false);
          subscription?.cancel();
        }
      });

      final success = await completer.future;

      if (success) {
        _updateState(ConnectionState.connected);
        _reconnectAttempts = 0;
        _startPingTimer();
      } else {
        _updateState(ConnectionState.error);
        disconnect();
      }

      return success;
    } catch (e) {
      _error = 'Connection error: $e';
      _updateState(ConnectionState.error);
      return false;
    }
  }

  /// Connect with pairing data
  Future<bool> connectWithPairing(PairingData pairingData) async {
    try {
      _updateState(ConnectionState.connecting);
      _error = null;

      final uri = Uri.parse(pairingData.websocketUrl);
      _channel = WebSocketChannel.connect(uri);

      // Listen to messages
      _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
      );

      // Send pairing message
      _sendRaw({
        'type': WsMessageType.pair,
        'session_id': pairingData.sessionId,
        'temp_token': pairingData.tempToken,
        'device_info': AppConstants.getDeviceInfo(),
      });

      // Wait for auth success
      final completer = Completer<bool>();
      StreamSubscription? subscription;

      subscription = _messageController.stream.listen((msg) {
        if (msg['type'] == WsMessageType.authSuccess) {
          if (!completer.isCompleted) {
            completer.complete(true);
            subscription?.cancel();
          }
        } else if (msg['type'] == WsMessageType.authError ||
            msg['type'] == WsMessageType.error) {
          if (!completer.isCompleted) {
            _error = msg['message'] as String? ?? 'Pairing failed';
            completer.complete(false);
            subscription?.cancel();
          }
        }
      });

      // Timeout after 10 seconds
      Future.delayed(const Duration(seconds: 10), () {
        if (!completer.isCompleted) {
          _error = 'Pairing timeout';
          completer.complete(false);
          subscription?.cancel();
        }
      });

      final success = await completer.future;

      if (success) {
        _updateState(ConnectionState.connected);
        _reconnectAttempts = 0;
        _startPingTimer();
      } else {
        _updateState(ConnectionState.error);
        disconnect();
      }

      return success;
    } catch (e) {
      _error = 'Connection error: $e';
      _updateState(ConnectionState.error);
      return false;
    }
  }

  /// Send a message
  void sendMessage(String content) {
    if (_state != ConnectionState.connected) {
      throw StateError('Not connected');
    }

    _sendRaw({
      'type': WsMessageType.message,
      'content': content,
    });
  }

  /// Disconnect
  void disconnect() {
    _pingTimer?.cancel();
    _pingTimer = null;
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
    _channel?.sink.close(status.normalClosure);
    _channel = null;
    _updateState(ConnectionState.disconnected);
  }

  /// Dispose resources
  void dispose() {
    disconnect();
    _messageController.close();
    _stateController.close();
  }

  // Private methods

  void _handleMessage(dynamic data) {
    try {
      final json = jsonDecode(data as String) as Map<String, dynamic>;

      // Handle pong
      if (json['type'] == WsMessageType.pong) {
        return; // Ignore pong messages
      }

      _messageController.add(json);
    } catch (e) {
      // Invalid JSON, ignore
    }
  }

  void _handleError(dynamic error) {
    _error = 'WebSocket error: $error';
    _updateState(ConnectionState.error);
    _scheduleReconnect();
  }

  void _handleDisconnect() {
    if (_state == ConnectionState.connected) {
      _updateState(ConnectionState.disconnected);
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= AppConstants.maxReconnectAttempts) {
      _error = 'Maximum reconnection attempts reached';
      return;
    }

    _reconnectTimer?.cancel();

    // Exponential backoff
    final delay = Duration(
      milliseconds: AppConstants.reconnectDelay.inMilliseconds *
          (1 << _reconnectAttempts),
    );

    final cappedDelay = delay > AppConstants.maxReconnectDelay
        ? AppConstants.maxReconnectDelay
        : delay;

    _reconnectTimer = Timer(cappedDelay, () {
      _reconnectAttempts++;
      // Auto-reconnect would need stored credentials
      // This is handled by the provider layer
    });
  }

  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(AppConstants.pingInterval, (_) {
      if (_state == ConnectionState.connected) {
        _sendRaw({'type': WsMessageType.ping});
      }
    });
  }

  void _sendRaw(Map<String, dynamic> data) {
    try {
      _channel?.sink.add(jsonEncode(data));
    } catch (e) {
      // Error sending, connection likely broken
      _handleError(e);
    }
  }

  void _updateState(ConnectionState newState) {
    _state = newState;
    _stateController.add(newState);
  }
}
