import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/providers/auth_provider.dart';
import '../../core/providers/websocket_provider.dart';
import '../../core/providers/messages_provider.dart';
import '../../core/api/websocket_client.dart' as ws;
import '../../theme/app_theme.dart';
import 'widgets/message_bubble.dart';
import 'widgets/message_input.dart';

class ChatScreen extends ConsumerWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final messages = ref.watch(messagesProvider);
    final wsState = ref.watch(websocketStateProvider);

    final isConnected = wsState.state == ws.ConnectionState.connected;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          children: [
            const Text('Entobot'),
            Text(
              _getStatusText(wsState.state),
              style: TextStyle(
                fontSize: 12,
                color: _getStatusColor(wsState.state),
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => context.push('/settings'),
            tooltip: 'Settings',
          ),
        ],
      ),
      body: Column(
        children: [
          // Connection error banner
          if (wsState.error != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(AppTheme.spacing12),
              color: AppTheme.errorColor.withOpacity(0.1),
              child: Row(
                children: [
                  Icon(
                    Icons.error_outline,
                    color: AppTheme.errorColor,
                    size: 20,
                  ),
                  const SizedBox(width: AppTheme.spacing8),
                  Expanded(
                    child: Text(
                      wsState.error!,
                      style: TextStyle(
                        color: AppTheme.errorColor,
                        fontSize: 13,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      ref.read(authProvider.notifier).refresh();
                    },
                    child: const Text('Retry'),
                  ),
                ],
              ),
            ),

          // Messages list
          Expanded(
            child: messages.isEmpty
                ? _buildEmptyState(context)
                : ListView.builder(
                    reverse: true,
                    padding: const EdgeInsets.symmetric(
                      vertical: AppTheme.spacing8,
                    ),
                    itemCount: messages.length,
                    itemBuilder: (context, index) {
                      final message = messages[messages.length - 1 - index];
                      return MessageBubble(message: message);
                    },
                  ),
          ),

          // Message input
          MessageInput(
            isConnected: isConnected,
            onSendMessage: (text) {
              ref.read(messagesProvider.notifier).addUserMessage(text);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppTheme.spacing32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.chat_bubble_outline,
              size: 64,
              color: theme.colorScheme.primary.withOpacity(0.3),
            ),
            const SizedBox(height: AppTheme.spacing16),
            Text(
              'No messages yet',
              style: theme.textTheme.titleLarge?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            const SizedBox(height: AppTheme.spacing8),
            Text(
              'Send a message to start chatting with Entobot',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.5),
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  String _getStatusText(ws.ConnectionState state) {
    switch (state) {
      case ws.ConnectionState.connected:
        return 'Online';
      case ws.ConnectionState.connecting:
        return 'Connecting...';
      case ws.ConnectionState.disconnected:
        return 'Offline';
      case ws.ConnectionState.error:
        return 'Connection Error';
    }
  }

  Color _getStatusColor(ws.ConnectionState state) {
    switch (state) {
      case ws.ConnectionState.connected:
        return AppTheme.successColor;
      case ws.ConnectionState.connecting:
        return Colors.orange;
      case ws.ConnectionState.disconnected:
      case ws.ConnectionState.error:
        return AppTheme.errorColor;
    }
  }
}
