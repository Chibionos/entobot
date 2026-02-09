import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/providers/auth_provider.dart';
import '../../theme/app_theme.dart';

class SecurityScreen extends ConsumerWidget {
  const SecurityScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Security'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppTheme.spacing16),
        children: [
          // Device Information
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.spacing16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.devices,
                        color: theme.colorScheme.primary,
                      ),
                      const SizedBox(width: AppTheme.spacing12),
                      Text(
                        'Device Information',
                        style: theme.textTheme.titleMedium,
                      ),
                    ],
                  ),
                  const Divider(height: 24),
                  _buildInfoRow(
                    context,
                    'Device ID',
                    authState.deviceId ?? 'Not available',
                    onTap: () {
                      if (authState.deviceId != null) {
                        Clipboard.setData(
                          ClipboardData(text: authState.deviceId!),
                        );
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Device ID copied to clipboard'),
                            duration: Duration(seconds: 1),
                          ),
                        );
                      }
                    },
                  ),
                  const SizedBox(height: AppTheme.spacing12),
                  _buildInfoRow(
                    context,
                    'Paired At',
                    authState.credentials?.pairedAt != null
                        ? DateFormat('MMM d, y - HH:mm')
                            .format(authState.credentials!.pairedAt)
                        : 'Not available',
                  ),
                  const SizedBox(height: AppTheme.spacing12),
                  _buildInfoRow(
                    context,
                    'WebSocket URL',
                    authState.credentials?.websocketUrl ?? 'Not available',
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: AppTheme.spacing16),

          // Security Actions
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.spacing16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.security,
                        color: theme.colorScheme.primary,
                      ),
                      const SizedBox(width: AppTheme.spacing12),
                      Text(
                        'Security Actions',
                        style: theme.textTheme.titleMedium,
                      ),
                    ],
                  ),
                  const Divider(height: 24),
                  ListTile(
                    leading: const Icon(Icons.lock_reset),
                    title: const Text('Re-pair Device'),
                    subtitle: const Text('Scan QR code again'),
                    onTap: () => _showRepairDialog(context, ref),
                    contentPadding: EdgeInsets.zero,
                  ),
                  ListTile(
                    leading: Icon(
                      Icons.logout,
                      color: AppTheme.errorColor,
                    ),
                    title: Text(
                      'Revoke Access',
                      style: TextStyle(color: AppTheme.errorColor),
                    ),
                    subtitle: const Text('Disconnect and clear credentials'),
                    onTap: () => _showRevokeDialog(context, ref),
                    contentPadding: EdgeInsets.zero,
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: AppTheme.spacing24),

          // Security Tips
          Card(
            color: theme.colorScheme.primaryContainer,
            child: Padding(
              padding: const EdgeInsets.all(AppTheme.spacing16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.info_outline,
                        color: theme.colorScheme.onPrimaryContainer,
                      ),
                      const SizedBox(width: AppTheme.spacing12),
                      Text(
                        'Security Tips',
                        style: theme.textTheme.titleSmall?.copyWith(
                          color: theme.colorScheme.onPrimaryContainer,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppTheme.spacing12),
                  Text(
                    '• Your credentials are stored securely on this device\n'
                    '• Never share your Device ID or QR codes with others\n'
                    '• Re-pair if you suspect unauthorized access\n'
                    '• Revoke access when changing devices',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onPrimaryContainer,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(
    BuildContext context,
    String label,
    String value, {
    VoidCallback? onTap,
  }) {
    final theme = Theme.of(context);

    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Expanded(
                  child: Text(
                    value,
                    style: theme.textTheme.bodyMedium,
                  ),
                ),
                if (onTap != null)
                  Icon(
                    Icons.copy,
                    size: 16,
                    color: theme.colorScheme.primary,
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _showRepairDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Re-pair Device'),
        content: const Text(
          'This will disconnect your current session and require you to scan a new QR code. Continue?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              await ref.read(authProvider.notifier).logout();
              if (context.mounted) {
                Navigator.of(context).popUntil((route) => route.isFirst);
              }
            },
            child: const Text('Re-pair'),
          ),
        ],
      ),
    );
  }

  void _showRevokeDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Revoke Access'),
        content: const Text(
          'This will permanently revoke this device\'s access token. '
          'You will need to pair again to reconnect. Continue?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              await ref.read(authProvider.notifier).logout();
              if (context.mounted) {
                Navigator.of(context).popUntil((route) => route.isFirst);
              }
            },
            child: Text(
              'Revoke',
              style: TextStyle(color: AppTheme.errorColor),
            ),
          ),
        ],
      ),
    );
  }
}
