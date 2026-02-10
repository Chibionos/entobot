import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../models/message.dart';
import '../utils/constants.dart';
import 'websocket_provider.dart';

const _uuid = Uuid();

/// Messages state notifier
class MessagesNotifier extends StateNotifier<List<Message>> {
  final Ref _ref;

  MessagesNotifier(this._ref) : super([]) {
    _listenToWebSocketMessages();
  }

  /// Listen to incoming WebSocket messages
  void _listenToWebSocketMessages() {
    _ref.listen(messagesStreamProvider, (previous, next) {
      next.when(
        data: (msg) {
          if (msg['type'] == WsMessageType.message) {
            final content = msg['content'] as String?;
            if (content != null && content.isNotEmpty) {
              addBotMessage(content);
            }
          }
        },
        loading: () {},
        error: (_, __) {},
      );
    });
  }

  /// Add user message
  void addUserMessage(String content) {
    final message = Message(
      id: _uuid.v4(),
      content: content,
      isUser: true,
      timestamp: DateTime.now(),
      status: MessageStatus.sending,
    );

    state = [...state, message];

    // Send via WebSocket
    try {
      final wsNotifier = _ref.read(websocketStateProvider.notifier);
      wsNotifier.sendMessage(content);

      // Update status to sent
      _updateMessageStatus(message.id, MessageStatus.sent);
    } catch (e) {
      // Update status to error
      _updateMessageStatus(message.id, MessageStatus.error);
    }
  }

  /// Add bot message
  void addBotMessage(String content) {
    final message = Message(
      id: _uuid.v4(),
      content: content,
      isUser: false,
      timestamp: DateTime.now(),
      status: MessageStatus.sent,
    );

    state = [...state, message];
  }

  /// Update message status
  void _updateMessageStatus(String messageId, MessageStatus status) {
    state = state.map((msg) {
      if (msg.id == messageId) {
        return msg.copyWith(status: status);
      }
      return msg;
    }).toList();
  }

  /// Clear all messages
  void clearMessages() {
    state = [];
  }

  /// Remove a specific message
  void removeMessage(String messageId) {
    state = state.where((msg) => msg.id != messageId).toList();
  }

  /// Retry sending failed message
  void retryMessage(String messageId) {
    final message = state.firstWhere((msg) => msg.id == messageId);

    if (message.status == MessageStatus.error) {
      _updateMessageStatus(messageId, MessageStatus.sending);

      try {
        final wsNotifier = _ref.read(websocketStateProvider.notifier);
        wsNotifier.sendMessage(message.content);
        _updateMessageStatus(messageId, MessageStatus.sent);
      } catch (e) {
        _updateMessageStatus(messageId, MessageStatus.error);
      }
    }
  }
}

/// Messages provider
final messagesProvider =
    StateNotifierProvider<MessagesNotifier, List<Message>>((ref) {
  return MessagesNotifier(ref);
});
